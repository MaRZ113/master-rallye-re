#!/usr/bin/env python3
"""COURSE-RENDER-FIX1: per-race lifecycle table and reflection verdict from the PS2 diagnostics stream.

Input  ps2diag-*.jsonl (RaceLedger=1; ps2_race_start / ps2_race_summary / ps2_effect_disabled / ps2_reflection_stage /
       ps2_reflection_order) and, optionally, the baseline session-*.jsonl (race epoch snapshots, classifier epoch).
Output a Markdown report and a JSON file. Exit code 0 = no finding, 1 = at least one finding (see "findings").

The baseline session log is capped at 16 MiB, which a long session of race -> menu -> race cycles exceeds after about
seven races; the ps2diag stream is separate (4 MiB cap) and holds one compact record per race. The analyzer therefore works
from the ps2diag stream and uses the session log only to cross-check generations.

Findings (each names the race, course and effect):
  EFFECT_LOST          an effect drew in an earlier race on a course it supports and draws nothing in a later race
  NO_DRAWS_ACTIVE      the pilot reports active/requested for the race but no draw outcome was counted
  DISABLED             a session-wide switch-off (ps2_effect_disabled) with its reason
  RESOURCE_GROWTH      tracked resources grow by more than the allowed amount per race
  GENERATION_ORDER     race generation does not increase, or request/successful generation disagree
  RACE_NOT_CLOSED      a race has a start record and no summary (log cut off or crash)
  REFLECTION_WORLD_INCOMPLETE  a stage report found the bottom third of the captured frame empty
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# Outcomes that mean "intentionally not drawn here" (course without asset, stock PC course, no certificate yet, ...).
INTENTIONAL = {
    'course_has_no_asset', 'stock_pc_course_no_loose_course_dx', 'not_a_spline_course', 'not_a_grass_course',
    'no_single_race_certificate', 'no_points_in_range', 'nothing_visible', 'no_pc_damage_row_this_frame', 'no_pc_gps_this_frame',
    'no_rows_this_frame', 'outside_race', 'turkey3_owner_or_camera_unverified', 'stock_pc_course_allowed_by_ini',
}
# Outcome that counts as a successful draw, per effect (substring match on the outcome key).
DRAWN = {
    'reflection_capture': ('inframe_ready', 'late_ready'),
    'reflection_body': ('applied',),
    'fleet': ('race_body', 'race_part'),
    'fleet_wheels': ('wheel',),
    'grass': ('drawn',),
    'shrubs': ('drawn',),
    'ground_detail': ('ground_detail_applied',),
    'water': ('replaced',),
    'spline': ('drawn',),
    'hud': ('drawn',),
    'postfx': ('blended', 'applied', 'drawn'),
    'models': ('xtrail', 'frontend_model', 'vehicle_partition', 'brake_lamp'),
}
# Pilot state key per effect (state_json of the summary).
STATE_KEY = {'grass': 'grass', 'shrubs': 'shrubs', 'spline': 'spline', 'water': 'water', 'reflection_capture': 'reflection',
             'reflection_body': 'reflection', 'ground_detail': 'ground_detail'}
# Effects that count an outcome only when a matching draw happened (no water on the course, car drawn by the fleet model):
# an empty outcome set is normal for them and is judged only against earlier races of the same course.
QUIET_WHEN_IDLE = {'water', 'reflection_body', 'ground_detail'}
FAILURE_WORDS = ('fail', 'unsupported', 'allocation', 'error', 'exception', 'lost', 'blocked')
RESOURCE_GROWTH_PER_RACE = 400


def load_jsonl(path: Path):
    records, bad = [], 0
    if not path or not path.is_file():
        return records, bad
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return records, bad


def drawn_count(effect: str, outcomes: dict) -> int:
    keys = DRAWN.get(effect, ('drawn',))
    return sum(n for k, n in outcomes.items() if any(w in k for w in keys) and not any(f in k for f in FAILURE_WORDS))


def failure_count(outcomes: dict) -> int:
    return sum(n for k, n in outcomes.items() if any(w in k for w in FAILURE_WORDS))


def summarize_race(rec: dict) -> dict:
    effects = rec.get('effects', {})
    row = {
        'seq': rec.get('seq'), 'course': rec.get('course'), 'race_generation': rec.get('race_generation'),
        'owner_lifetime': rec.get('owner_lifetime'), 'frames': rec.get('frames', 0), 'end_reason': rec.get('end_reason'),
        'epoch': rec.get('epoch', {}), 'state': rec.get('state', {}), 'effects': {}, 'draws': {}, 'failures': {}, 'intentional': {},
    }
    for effect, outcomes in effects.items():
        row['effects'][effect] = outcomes
        row['draws'][effect] = drawn_count(effect, outcomes)
        row['failures'][effect] = failure_count(outcomes)
        row['intentional'][effect] = sum(n for k, n in outcomes.items() if k in INTENTIONAL)
    return row


def pilot_expected_active(row: dict, effect: str) -> bool:
    """The pilot state at the end of the race says the effect was configured and running (not intentionally off)."""
    key = STATE_KEY.get(effect)
    state = row['state'].get(key) if key else None
    if not isinstance(state, dict):
        return False
    return bool(state.get('active')) and bool(state.get('requested', state.get('active')))


def analyze(diag_records, session_records=None, min_frames=120):
    findings, rows = [], []
    starts = {}
    disables = []
    stages, orders = [], []
    for rec in diag_records:
        kind = rec.get('type')
        if kind == 'ps2_race_start':
            starts[rec.get('seq')] = rec
        elif kind == 'ps2_race_summary':
            rows.append(summarize_race(rec))
        elif kind == 'ps2_effect_disabled':
            disables.append(rec)
        elif kind == 'ps2_reflection_stage':
            stages.append(rec)
        elif kind == 'ps2_reflection_order':
            orders.append(rec)

    closed = {r['seq'] for r in rows}
    for seq, start in starts.items():
        if seq not in closed:
            findings.append({'code': 'RACE_NOT_CLOSED', 'race_seq': seq, 'course': start.get('course'),
                             'detail': 'start record without summary (log cut off, crash or game still running)'})

    # Per effect: draws by course over time -> loss detection.
    seen_draw = defaultdict(dict)       # effect -> course -> first race seq with draws
    last_draw_seq = {}                  # effect -> seq of the last race that drew
    effects_present = set()
    for row in rows:
        effects_present.update(row['effects'])
    for row in rows:
        for effect in effects_present:
            draws = row['draws'].get(effect, 0)
            if draws:
                seen_draw[effect].setdefault(row['course'], row['seq'])
                last_draw_seq[effect] = row['seq']
    for row in rows:
        if row['frames'] < min_frames:
            continue
        for effect in sorted(effects_present):
            draws = row['draws'].get(effect, 0)
            if draws:
                continue
            outcomes = row['effects'].get(effect, {})
            intentional_only = outcomes and all(k in INTENTIONAL for k in outcomes)
            earlier = seen_draw[effect].get(row['course'])
            if earlier is not None and earlier < row['seq'] and not intentional_only:
                findings.append({'code': 'EFFECT_LOST', 'race_seq': row['seq'], 'course': row['course'], 'effect': effect,
                                 'detail': f"drew in race {earlier} on the same course, nothing in this race: {outcomes or 'no outcome counted'}"})
            elif (pilot_expected_active(row, effect) and not intentional_only and effect not in ('hud', 'postfx') and
                  (outcomes or effect not in QUIET_WHEN_IDLE)):
                findings.append({'code': 'NO_DRAWS_ACTIVE', 'race_seq': row['seq'], 'course': row['course'], 'effect': effect,
                                 'detail': f"pilot active/requested, outcomes: {outcomes or 'none counted'}"})
    # An effect that stops for good on courses that supported it earlier.
    for effect, courses in seen_draw.items():
        last = last_draw_seq.get(effect, 0)
        later = [r for r in rows if r['seq'] > last and r['frames'] >= min_frames and r['course'] in courses]
        for row in later:
            if not any(f['code'] == 'EFFECT_LOST' and f['race_seq'] == row['seq'] and f['effect'] == effect for f in findings):
                findings.append({'code': 'EFFECT_LOST', 'race_seq': row['seq'], 'course': row['course'], 'effect': effect,
                                 'detail': f'no draw since race {last}'})

    for event in disables:
        findings.append({'code': 'DISABLED', 'race_generation': event.get('race_generation'), 'course': event.get('course'),
                         'effect': event.get('effect'), 'detail': event.get('reason')})

    previous_tracked = None
    previous_generation = 0
    previous_end = None
    for row in rows:
        resources = row['state'].get('resources', {})
        tracked = resources.get('tracked')
        if isinstance(tracked, int):
            if previous_tracked is not None and tracked - previous_tracked > RESOURCE_GROWTH_PER_RACE:
                findings.append({'code': 'RESOURCE_GROWTH', 'race_seq': row['seq'], 'course': row['course'],
                                 'detail': f'tracked resources {previous_tracked} -> {tracked}'})
            previous_tracked = tracked
        generation = row.get('race_generation') or 0
        # the same generation twice is a race that was closed and reopened (hud absent for a moment): not an order error
        if generation < previous_generation or (generation == previous_generation and previous_end != 'race_left'):
            findings.append({'code': 'GENERATION_ORDER', 'race_seq': row['seq'], 'course': row['course'],
                             'detail': f'race generation {generation} after {previous_generation}'})
        previous_generation = max(previous_generation, generation)
        previous_end = row.get('end_reason')
        epoch = row.get('epoch', {})
        if 'request_generation' in epoch and 'successful_generation' in epoch and epoch['request_generation'] != epoch['successful_generation']:
            findings.append({'code': 'GENERATION_ORDER', 'race_seq': row['seq'], 'course': row['course'],
                             'detail': f"request_generation {epoch['request_generation']} != successful_generation {epoch['successful_generation']}"})

    reflection = reflection_verdict(stages, orders)
    for item in reflection['stages']:
        if item['world_incomplete'] and not item['late']:
            findings.append({'code': 'REFLECTION_WORLD_INCOMPLETE', 'race_generation': item['race_generation'], 'course': item['course'],
                             'detail': f"in-frame capture {item['ordinal']}: bottom third of the PS2 frame {item['bottom_black']:.0%} black"})

    session = session_cross_check(session_records or [], rows)
    return {'races': rows, 'findings': findings, 'reflection': reflection, 'session': session,
            'disables': [{k: d.get(k) for k in ('effect', 'reason', 'race_generation', 'course', 'frame')} for d in disables]}


GROUND_FVF = {'578', '594'}   # D3DFVF_XYZ|DIFFUSE|TEX2 (+NORMAL): ground with the second (noise) UV set


def fvf_totals(block: dict):
    fvf = block.get('fvf', {})
    ground = sum(v[1] for k, v in fvf.items() if k in GROUND_FVF)
    return block.get('triangles', 0), ground, block.get('draws', 0)


def reflection_verdict(stages, orders):
    out_stage = []
    for s in stages:
        bottom = s.get('bottom_third', {})
        out_stage.append({
            'race_generation': s.get('race_generation'), 'course': s.get('course'), 'frame': s.get('frame'), 'ordinal': s.get('ordinal'),
            'late': bool(s.get('late')), 'timing': s.get('timing'), 'timing_now': s.get('timing_now'),
            'world_incomplete': bool(s.get('world_incomplete')), 'bottom_black': bottom.get('black', 0.0),
            'source_black': s.get('source', {}).get('black', 0.0), 'env_dynamic_mean': s.get('dynamic', {}).get('mean'),
            'env_hash': s.get('env', {}).get('hash'), 'served': s.get('served', {}), 'readback_ok': s.get('readback_ok'),
            'png': s.get('png'), 'reason': s.get('reason'),
        })
    out_order = []
    for o in orders:
        before_tris, before_ground, before_draws = fvf_totals(o.get('before_capture', {}))
        total_tris, total_ground, total_draws = fvf_totals(o.get('frame_total', {}))
        out_order.append({
            'frame': o.get('frame'), 'late': bool(o.get('late')), 'draws_before': before_draws, 'draws_total': total_draws,
            'triangles_before': before_tris, 'triangles_total': total_tris,
            'ground_triangles_before': before_ground, 'ground_triangles_total': total_ground,
            'ground_before_fraction': (before_ground / total_ground) if total_ground else None,
        })
    by_course = defaultdict(lambda: {'stages': 0, 'incomplete': 0, 'late_races': set()})
    for s in out_stage:
        c = by_course[s['course']]
        c['stages'] += 1
        c['incomplete'] += 1 if (s['world_incomplete'] and not s['late']) else 0
        if s['late']:
            c['late_races'].add(s['race_generation'])
    for c in by_course.values():
        c['late_races'] = sorted(c['late_races'])
    return {'stages': out_stage, 'orders': out_order, 'by_course': dict(by_course)}


def session_cross_check(records, rows):
    info = {'records': len(records)}
    if not records:
        return info
    frames = [r.get('frame') for r in records if r.get('type') == 'frame_summary']
    epochs = [r.get('classifier', {}).get('epoch') for r in records if r.get('type') == 'frame_summary']
    snaps = [r for r in records if r.get('type') == 'race_epoch_snapshot']
    info.update({
        'last_frame_summary': frames[-1] if frames else None,
        'classifier_epoch_first_last': [epochs[0], epochs[-1]] if epochs else None,
        'snapshots': len(snaps),
        'certified_generations': sorted({s.get('race_lifecycle_generation') for s in snaps if s.get('live_certificate_valid')}),
        'awaiting_race_owner_in_certified': sum(1 for s in snaps if s.get('live_certificate_valid') and s.get('state') == 'AWAITING_RACE_OWNER'),
        'summaries_in_ps2diag': len(rows),
    })
    return info


def markdown(result: dict) -> str:
    rows = result['races']
    lines = ['# COURSE-RENDER-FIX1 race lifecycle report', '']
    lines.append(f"Races with a summary: {len(rows)}; findings: {len(result['findings'])}; session-wide switch-offs: {len(result['disables'])}")
    lines.append('')
    effects = []
    for row in rows:
        for e in row['effects']:
            if e not in effects:
                effects.append(e)
    header = ['#', 'course', 'gen', 'owner', 'frames', 'end'] + effects
    lines.append('| ' + ' | '.join(header) + ' |')
    lines.append('|' + '---|' * len(header))
    for row in rows:
        cells = [str(row['seq']), str(row['course']).replace('RaceTest/', ''), str(row['race_generation']), str(row['owner_lifetime']),
                 str(row['frames']), str(row['end_reason'])]
        for e in effects:
            outcomes = row['effects'].get(e)
            if not outcomes:
                cells.append('-')
                continue
            d, f, i = row['draws'].get(e, 0), row['failures'].get(e, 0), row['intentional'].get(e, 0)
            cells.append(f"{d}" + (f" /F{f}" if f else '') + (f" /off{i}" if i and not d else ''))
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines.append('')
    lines.append('Cell: draws counted (success outcomes), /F = failure outcomes, /off = intentional gate outcomes (course without asset, stock course).')
    lines.append('')
    if result['findings']:
        lines.append('## Findings')
        for f in result['findings']:
            where = f"race {f['race_seq']}" if 'race_seq' in f else f"generation {f.get('race_generation')}"
            lines.append(f"- **{f['code']}** {where} {f.get('course') or ''} {f.get('effect') or ''}: {f.get('detail')}")
        lines.append('')
    ref = result['reflection']
    if ref['stages']:
        lines.append('## Reflection stage reports')
        lines.append('| race gen | course | frame | n | mode | late | bottom third black | source black | served | world incomplete |')
        lines.append('|---|---|---|---|---|---|---|---|---|---|')
        for s in ref['stages']:
            lines.append(f"| {s['race_generation']} | {str(s['course']).replace('RaceTest/', '')} | {s['frame']} | {s['ordinal']} | {s['timing_now']} | "
                         f"{'yes' if s['late'] else 'no'} | {s['bottom_black']:.0%} | {s['source_black']:.0%} | {s['served'].get('frame_count')} | "
                         f"{'YES' if s['world_incomplete'] else 'no'} |")
        lines.append('')
    if ref['orders']:
        lines.append('## Draw order at the environment capture')
        lines.append('| frame | late | draws before / total | triangles before / total | ground (0x242/0x252) triangles before / total |')
        lines.append('|---|---|---|---|---|')
        for o in ref['orders']:
            lines.append(f"| {o['frame']} | {'yes' if o['late'] else 'no'} | {o['draws_before']} / {o['draws_total']} | {o['triangles_before']} / {o['triangles_total']} | "
                         f"{o['ground_triangles_before']} / {o['ground_triangles_total']} |")
        lines.append('')
    if result['session'].get('records'):
        lines.append('## Session log cross-check')
        lines.append('```json')
        lines.append(json.dumps(result['session'], indent=1))
        lines.append('```')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--diag', type=Path, required=True, help='ps2diag-*.jsonl')
    parser.add_argument('--session', type=Path, help='session-*.jsonl of the same run (optional cross-check)')
    parser.add_argument('--json', type=Path, help='write the full result as JSON')
    parser.add_argument('--md', type=Path, help='write the Markdown report')
    parser.add_argument('--min-races', type=int, default=0, help='fail when fewer race summaries exist')
    parser.add_argument('--min-frames', type=int, default=120, help='races shorter than this are not judged for lost effects')
    args = parser.parse_args(argv)
    diag, bad = load_jsonl(args.diag)
    session, _ = load_jsonl(args.session) if args.session else ([], 0)
    result = analyze(diag, session, args.min_frames)
    result['unparsable_lines'] = bad
    if len(result['races']) < args.min_races:
        result['findings'].append({'code': 'TOO_FEW_RACES', 'detail': f"{len(result['races'])} summaries, {args.min_races} required"})
    text = markdown(result)
    if args.md:
        args.md.write_text(text, encoding='utf-8')
    else:
        sys.stdout.write(text)
    if args.json:
        args.json.write_text(json.dumps(result, indent=1, default=list), encoding='utf-8')
    return 1 if result['findings'] else 0


if __name__ == '__main__':
    sys.exit(main())
