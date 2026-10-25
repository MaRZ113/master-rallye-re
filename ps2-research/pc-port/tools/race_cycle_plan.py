#!/usr/bin/env python3
"""COURSE-RENDER-FIX1: the repeatable race-cycle sequence (12 or more race entries) and its check against a ps2diag stream.

  python race_cycle_plan.py plan  --entries 14 --md plan.md --json plan.json
  python race_cycle_plan.py check --plan plan.json --diag ps2diag-....jsonl

The plan drives ONE car (the same vehicle on every course, so reflections are comparable) through converted PS2 course
packages (loose course DX: SpainS2, Turkey3, Turkey2, France1) and stock PC courses (Italy3, Spain2, ItalyM1) as controls.
The converted courses come back several times, so a loss that only appears after N race entries is visible per course.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# (course id as the race certificate names it, kind, what the entry shows)
BASE = [
    ('RaceTest/SpainS2', 'converted', 'black reflection candidate; PS2 water (12 triangles); boats (spline objects); grass'),
    ('RaceTest/Italy3', 'stock', 'control: stock PC course on the same car; spline gate must say stock course, grass/shrubs'),
    ('RaceTest/Turkey3', 'converted', 'PS2 water (26 triangles), grass and shrubs, converted course'),
    ('RaceTest/France1', 'converted', 'converted course with boats; waterfall'),
    ('RaceTest/SpainS2', 'converted', 'second entry of the candidate: every effect must come back'),
    ('RaceTest/Italy3', 'stock', 'second control entry'),
    ('RaceTest/Turkey3', 'converted', 'second entry: water, grass, shrubs'),
    ('RaceTest/Spain2', 'stock', 'stock course with water (PS2 water on retail geometry)'),
    ('RaceTest/SpainS2', 'converted', 'third entry'),
    ('RaceTest/Turkey2', 'converted', 'converted course, puddles'),
    ('RaceTest/ItalyM1', 'stock', 'stock control'),
    ('RaceTest/Turkey3', 'converted', 'third entry'),
    ('RaceTest/SpainS2', 'converted', 'fourth entry'),
    ('RaceTest/France1', 'converted', 'second entry'),
]
MIN_FRAMES = 600   # about ten seconds at 60 fps


def build_plan(entries: int):
    if entries < 12:
        raise SystemExit('the plan needs at least 12 race entries')
    plan = []
    for i in range(entries):
        course, kind, note = BASE[i % len(BASE)]
        plan.append({'entry': i + 1, 'course': course, 'kind': kind, 'note': note, 'min_frames': MIN_FRAMES})
    return plan


def markdown(plan) -> str:
    lines = ['# Race cycle plan (COURSE-RENDER-FIX1)', '',
             'One car for the whole run. In every entry: start the race, wait for the countdown, drive straight for ten seconds,',
             'steer left and right once, then Esc -> Quit to the menu and pick the next course. Do not restart the game between',
             'entries. If a screenshot is wanted (ReflectionDebug=2 shows the env target at the top of the screen) take it at',
             'second 5 of the entry.', '',
             '| # | course | kind | what it shows |', '|---|---|---|---|']
    for item in plan:
        lines.append(f"| {item['entry']} | {item['course'].replace('RaceTest/', '')} | {item['kind']} | {item['note']} |")
    lines += ['', f'Each entry must last at least {MIN_FRAMES} frames to be judged.', '',
              'After the run:', '', '    python tools/analyze_race_lifecycle.py --diag logs/ps2diag-*.jsonl --session logs/session-*.jsonl --md report.md --min-races 12',
              '    python tools/race_cycle_plan.py check --plan plan.json --diag logs/ps2diag-*.jsonl', '']
    return '\n'.join(lines)


def check(plan, records):
    summaries = [r for r in records if r.get('type') == 'ps2_race_summary']
    problems = []
    if len(summaries) < len(plan):
        problems.append(f'{len(summaries)} race summaries for {len(plan)} planned entries')
    for item, summary in zip(plan, summaries):
        if summary.get('course') != item['course']:
            problems.append(f"entry {item['entry']}: expected {item['course']}, the log has {summary.get('course')}")
        if summary.get('frames', 0) < item['min_frames']:
            problems.append(f"entry {item['entry']} ({item['course']}): only {summary.get('frames', 0)} frames (min {item['min_frames']})")
    generations = [s.get('race_generation', 0) for s in summaries]
    if generations != sorted(set(generations)):
        problems.append('race generations are not strictly increasing')
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('plan')
    p.add_argument('--entries', type=int, default=14)
    p.add_argument('--md', type=Path)
    p.add_argument('--json', type=Path)
    c = sub.add_parser('check')
    c.add_argument('--plan', type=Path, required=True)
    c.add_argument('--diag', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == 'plan':
        plan = build_plan(args.entries)
        text = markdown(plan)
        (args.md.write_text(text, encoding='utf-8') if args.md else sys.stdout.write(text))
        if args.json:
            args.json.write_text(json.dumps(plan, indent=1), encoding='utf-8')
        return 0
    plan = json.loads(args.plan.read_text(encoding='utf-8'))
    records = []
    for line in args.diag.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    problems = check(plan, records)
    for line in problems:
        print('PROBLEM', line)
    print('plan matches the log' if not problems else f'{len(problems)} problems')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
