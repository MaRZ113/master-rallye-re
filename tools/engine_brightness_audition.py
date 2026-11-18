"""AUDIO-RALLY1: engine brightness A/B through the original MR engine DSP (Unicorn, tools/vehicle_audio_audition.py).

The native generator (005A7C30) is a state-variable filter; its output mixes dry / low-pass / band-pass by the
second synthesis table rows 3 / 4 / 5 (005A7950; 205 = unity). Presets scale those rows; everything else is stock.
"""
import copy, hashlib, json, math, struct, sys
from pathlib import Path
V = Path(r'D:/Game/Master Rallye/master-rallye-re-v-cap'); sys.path[:0] = [str(V / 'src'), str(V / 'tools')]
import vehicle_audio_audition as va
from master_rallye.addon_sdk.audio_profile import decode_pcm, canonical_wav
from master_rallye.vehicle_physics_binding import parse_pe32_layout

EXE = Path(r'D:/Game/Master Rallye/MRallye.exe').read_bytes()
OUT = Path(r'D:/Game/Master Rallye/master-rallye-re-base/.research-output/hosts/host-rcx-01/audition-engine-brightness')
PRESETS = {'1-stock': ((1., 1., 1.), 1.), '2-clean': ((.55, .55, .55), 1.), '3-clean-pitched': ((.55, .55, .55), None)}
SHIFT = {'MR-Megane': 1.6, 'MR-Navara': 1.6, 'RCX-EvoVI': 1.8}
SOURCES = [('MR-Megane', Path(r'D:/Game/Master Rallye/DataAudio/vehicles/engine3.wav'), 18),
           ('MR-Navara', Path(r'D:/Game/Master Rallye/DataAudio/vehicles/rev9.wav'), 7),
           ('RCX-EvoVI', Path(r'D:/Game/Master Rallye/master-rallye-re-base/.research-output/hosts/host-rcx-01/MRMods/Vehicles/active/resources/DataAudio/vehicles/sdk/rcx_evo6/engine.wav'), 18)]
RPMS = [1200, 2500, 3800, 5000, 6200, 7000]
real_load = va.load_stock_audio_profiles
real_machine = va.machine
va.machine = lambda exe: real_machine(EXE)   # emulator image = retail; the preset tables are read from the passed copy
layout = parse_pe32_layout(EXE)


def preset_exe(group, scale):
    m, rows = real_load(); t = m['curve_table_groups'][group]
    exe = bytearray(EXE); at = layout.va_to_file_offset(int(t['second_va'], 16))
    vals = list(struct.unpack_from('<60H', exe, at))
    for row, k in zip((3, 4, 5), scale):
        for i in range(9):                        # entry 9 is the 65535 sentinel
            vals[row * 10 + i] = max(0, min(1200, round(vals[row * 10 + i] * k)))
    struct.pack_into('<60H', exe, at, *vals)
    first = layout.va_to_file_offset(int(t['first_va'], 16))
    sha = hashlib.sha256(bytes(exe[first:first + 120]) + bytes(exe[at:at + 120])).hexdigest()
    return bytes(exe), sha, vals[30:59]


report = {}
OUT.mkdir(parents=True, exist_ok=True)
for name, path, tuning in SOURCES:
    samples, fmt = decode_pcm(path.read_bytes())
    if fmt['sample_rate'] != 48000 or fmt['channels'] != 1: raise SystemExit(f'{name}: not 48 kHz mono')
    wav = canonical_wav(samples[:192000])
    m0, rows0 = real_load(); group = rows0[tuning]['curve_group']
    for preset, (scale, shift) in PRESETS.items():
        k = SHIFT[name] if shift is None else shift
        if k != 1.:                                  # pitch the loop up, cyclic linear resampling (stays a seamless loop)
            import numpy as np
            x = np.asarray(samples, float); n = int(round(len(x) / k)); t = np.arange(n) * (len(x) / n)
            y = np.interp(t, np.arange(len(x) + 1), np.append(x, x[0]))
            wav_used = canonical_wav([int(v) for v in np.clip(np.round(y), -32768, 32767)])
        else:
            wav_used = wav
        exe, sha, rows = preset_exe(group, scale)
        def patched_load(*a, _sha=sha, _g=group, **k):
            m, r = real_load(*a, **k); m = copy.deepcopy(m); m['curve_table_groups'][_g]['sha256_concatenated'] = _sha; return m, r
        va.load_stock_audio_profiles = patched_load
        data, rep = va.audition(exe, wav_used, stock_audio_profile_id=tuning, rpms=RPMS, rev_limit=7500, seconds=.8)
        va.load_stock_audio_profiles = real_load
        (OUT / f'{name}_{preset}.wav').write_bytes(data)
        pcm, _ = decode_pcm(data)
        # crude brightness measure: share of energy above ~2 kHz (first difference ~ high-pass)
        import numpy as np
        x = np.asarray(pcm, dtype=float); spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2; f = np.fft.rfftfreq(len(x), 1 / 48000)
        centroid = float((spec * f).sum() / spec.sum()); hf = float(spec[f > 2000].sum() / spec.sum())
        e = float((x * x).sum()) or 1
        clip = sum(1 for v in pcm if abs(v) >= 32767)
        report[f'{name}_{preset}'] = {'group': group, 'rms': round(math.sqrt(e / len(pcm))), 'centroid_hz': round(centroid), 'above_2k': round(hf, 3), 'clipped': clip,
                                      'peak': max(abs(v) for v in pcm)}
        print(name, preset, report[f'{name}_{preset}'])
(OUT / 'report.json').write_text(json.dumps({'presets': PRESETS, 'rpms': RPMS, 'seconds_per_step': .8, 'results': report, 'shift': SHIFT}, indent=1))
