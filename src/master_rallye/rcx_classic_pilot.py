"""Rally Championship Xtreme (PC) cars -> MR Classic native projects.

Same owner policy and pipeline as the TXR3 / Evo pilots (txr3_classic_pilot.create_pilot):
source geometry, source wheels and true dimensions (metres, no rescale, source track),
source diffuse textures with the stock MR material of each semantic role.

Roles come from the RCX part name, texture and QTO material flags:
flags 0x80 on the exterior atlas = painted/reflective panel (MR paint), 0x08 = transparent
(windows), the wheel textures split into tyre (tread, wall) / rim (chrome) / disc (trim).

Frontend classes by category (owner 2026-11-16): WRC, KIT CAR, CLASSIC. Native donor: retail MR
"Megane"; its physics values are replaced from the RCX PC car table (balance_physics).
"""
from __future__ import annotations
from . import txr3_classic_pilot as base

INTERIOR_PARTS = {'interior', 'dashboard', 'steering wheel', 'driver', 'driver head', 'co-driver', 'co-driver head'}


def _role(material):
    part = material.get('object', ''); tex = material.get('texture', ''); flags = material.get('flags_raw', 0)
    if part == 'windows': return 'glass'
    if part.startswith('brakelight'): return 'brake'
    if part.startswith('headlamp'): return 'lamp'
    if part.startswith('wiper'): return 'trim'
    if part.startswith('wheel'):
        if tex.startswith(('tread', 'wall', 'wheel .', 'wheel.', 'wheel a')): return 'tyre'
        if tex.startswith('disc'): return 'trim'
        return 'chrome'
    if part in INTERIOR_PARTS or tex.startswith(('interior', 'drivers', 'vinyl', 'sunstrip')): return 'interior'
    if tex.startswith('exterior') and flags & 0x80: return 'paint'
    return 'trim'


# key: family, display name, manufacturer, model, results, MR frontend class, bhp (RCX spec text), drive
CARS = {
    'IMPREZA00': ('RcxImpreza2000', 'Subaru Impreza WRC 2000', 'SUBARU', 'IMPREZA WRC 2000', 'SUBARU IMPREZA', 'WRC', 300, '4WD'),
    'ASTRA': ('RcxAstraKitCar', 'Vauxhall Astra Kit Car', 'VAUXHALL', 'ASTRA KIT CAR', 'VAUXHALL ASTRA', 'KIT CAR', 280, 'FWD'),
    'SAXO': ('RcxSaxo', 'Citroen Saxo', 'CITROEN', 'SAXO', 'CITROEN SAXO', 'KIT CAR', 215, 'FWD'),
    'MINI': ('RcxMiniCooper', 'Mini Cooper', 'MINI', 'COOPER', 'MINI COOPER', 'CLASSIC', 115, 'FWD'),
    'PUMA': ('RcxFordPuma', 'Ford Puma', 'FORD', 'PUMA', 'FORD PUMA', 'KIT CAR', 115, 'FWD'),
    'FOCUS': ('RcxFordFocusWrc', 'Ford Focus WRC', 'FORD', 'FOCUS WRC', 'FORD FOCUS', 'WRC', 300, '4WD'),
    'EVO6': ('RcxLancerEvo6', 'Mitsubishi Lancer Evo VI', 'MITSUBISHI', 'LANCER EVO VI', 'MITSUBISHI LANCER', 'WRC', 300, '4WD'),
    'P206': ('RcxPeugeot206Wrc', 'Peugeot 206 WRC', 'PEUGEOT', '206 WRC', 'PEUGEOT 206', 'WRC', 300, '4WD'),
    'QUATTRO': ('RcxAudiQuattro', 'Audi Quattro', 'AUDI', 'QUATTRO', 'AUDI QUATTRO', 'CLASSIC', 370, '4WD'),
}
ARCHIVES = {'IMPREZA00': 'subaru impreza00.rcx', 'ASTRA': 'Astra.rcx', 'SAXO': 'Citroen Saxo.rcx', 'MINI': 'Mini Cooper.rcx',
            'PUMA': 'Ford Puma.rcx', 'FOCUS': 'ford focus.rcx', 'EVO6': 'Lancer Evo6.rcx', 'P206': 'peugeot206.rcx',
            'QUATTRO': 'audi_quattro.rcx'}
# CarStats name of each car = the record key of the Rally.exe car table (read_pc_car_table)
COG = {'IMPREZA00': 'subaru impreza00', 'ASTRA': 'astra', 'SAXO': 'Citroen Saxo', 'MINI': 'Mini Cooper', 'PUMA': 'ford puma',
       'FOCUS': 'ford focus', 'EVO6': 'lancer evo6', 'P206': 'peugeot206', 'QUATTRO': 'audi_quattro'}

for key, (family, name, make, model, results, cls, bhp, drive) in CARS.items():
    base.VEHICLES[key] = {
        'family': family, 'name': name + ' (RCX)', 'manufacturer': make, 'model': model, 'results': results,
        'donor': 'Megane', 'audio': 18, 'class': 'T2', 'target_class': 'RCX ' + cls,
        'power': {'bhp': bhp, 'drive': drive, 'class': cls},
        'label': 'RCX', 'source_label': 'Rally Championship Xtreme (PC)', 'source_format': 'RCX Universal Vehicle Scene',
        'adapter_id': 'rcx-pc/1', 'long_axis': 11, 'role_fn': _role, 'glass_key': 'mat-body-windows-00',
        'keep_source_scale': True, 'source_track': True, 'lens_textures': True,
        'brake_evidence': 'RCX brakelight l/r parts (exterior atlas).'}

RALLY_EXE = 'E:/RallyWorkshop_Sources/sources/Rally Championship Xtreme/Rally.exe'


def read_pc_car_table(exe_path=RALLY_EXE):
    """The Rally.exe (PC, efc94948) car definition table: 28 records of 696 bytes; F = the final-drive array of
    record k at file 0xAA1F0 + 696 k. Same field order as the PS2 CAR_DEFINITION (STABS) in this part.
    Offsets from F (4-byte fields, floats unless noted):
      -0x148 name, -0x144 sound code, -0x140 CarStats (.cog) name, -0x13c small icon (char *);
      -78 EngineSound (u32), -75 TorqueSplit (1 = front only, 0 = rear only), -74 TorqueBoost, -59 Mass (kg),
      -28..-22 power_curve (engine torque over 7 even rpm steps; an 8th entry is 0), -12 num_gears (u32, counts
      reverse and neutral), -11..-4 gear_ratio (R, N placeholder, forward), +0..+4 final_drive (set-up choices),
      +81 redline, +83 idle, +84 wheel_radius.
    The PC kit cars share one torque curve and gearbox and the WRCs another; TorqueBoost and mass set them apart."""
    import struct
    b = open(exe_path, 'rb').read()
    f0, base_va, out = 0xAA1F0, 0x400000, {}
    s = lambda va: b[va - base_va:b.index(b'\0', va - base_va)].decode('latin1') if 0x4A0000 <= va < 0x4C0000 else None
    fl = lambda o: struct.unpack_from('<f', b, o)[0]
    u = lambda o: struct.unpack_from('<I', b, o)[0]
    for k in range(28):
        f = f0 + 696 * k
        name = s(u(f - 0x148))
        if name is None: break
        cog = s(u(f - 0x140)) or name
        ng = u(f - 12 * 4)
        out[cog] = {'name': name, 'sound_code': s(u(f - 0x144)), 'record': k, 'engine_sound': u(f - 78 * 4),
                    'torque_split': fl(f - 75 * 4), 'torque_boost': fl(f - 74 * 4), 'mass': fl(f - 59 * 4),
                    'power_curve': [fl(f + 4 * j) for j in range(-28, -21)],
                    'gears_reverse': fl(f - 11 * 4), 'gears_forward': [fl(f + 4 * j) for j in range(-9, -11 + ng)],
                    'final_drive': [fl(f + 4 * j) for j in range(5)],
                    'redline': fl(f + 81 * 4), 'idle': fl(f + 83 * 4), 'wheel_radius': fl(f + 84 * 4)}
    return out


# Donor reference: retail MR Megane = 350 Nm PeakTorque at rev limit 6500. Its RCX counterpart (renault megane:
# kit curve peak 400 x TorqueBoost 1.15 = 460, redline 8500) sets the scale: the same power when an RCX car runs
# to its own redline, PeakTorque = 350 * (peak / 460) * (6500 / redline).
DONOR_TORQUE, DONOR_REV, RCX_DONOR_PEAK = 350., 6500., 460.
DEFAULT_FINAL_DRIVE = 2          # middle of the five RCX final-drive choices (the default set-up)
# DRIVE1 (owner 2026-11-16): the Puma is the test car for the native drive layout (DriveType) and a 6-speed box.
DRIVE1_PILOTS = {'PUMA'}


def _geometric(first, last, n):
    return [first * (last / first) ** (i / (n - 1)) for i in range(n)]


def balance_physics(physics, key, wheel_radius, table=None):
    """MR vehicles.xml values from the RCX PC car table: mass, torque level and curve shape, rev range, gearbox
    and final drive. MR keeps 5 forward gears (Engine/Gears = 7: R, N, 5 forward; the SDK does not change array
    sizes): RCX 6-speed boxes keep their first and top gear with the steps between spread geometrically, the
    4-speed Mini gets one step inserted the same way. Final drive is scaled by the model's wheel radius vs the RCX
    one, so the road speed per engine rev is RCX's. Drive layout is recorded only (every retail MR car is
    DriveType 0; RCX TorqueSplit 1 = FWD, 0.35-0.5 = 4WD, 0 = RWD)."""
    table = table or read_pc_car_table()
    rec = table[COG[key]]
    values = physics['overrides'][next(iter(physics['overrides']))]
    curve = [v * rec['torque_boost'] for v in rec['power_curve']]
    peak, redline = max(curve), rec['redline']
    values['Chassis/TotalMass'] = rec['mass']
    values['Engine/PeakTorque'] = round(DONOR_TORQUE * peak / RCX_DONOR_PEAK * DONOR_REV / redline, 1)
    values['Engine/RevLimit'] = redline
    values['Engine/IdleRevs'] = rec['idle']
    for i in range(6):                       # MR torque table: (rev fraction, torque fraction) at 0, 0.2 .. 1.0
        x = i / 5 * (len(curve) - 1); j = min(int(x), len(curve) - 2); t = x - j
        values['Engine/TorqueEntry%d' % i] = [round(i / 5, 2), round((curve[j] * (1 - t) + curve[j + 1] * t) / peak, 3)]
    fwd = rec['gears_forward']
    split = rec['torque_split']
    layout = 'FWD' if split >= .99 else 'RWD' if split <= .01 else '4WD'
    pilot = key in DRIVE1_PILOTS
    # DRIVE1 pilot: the real RCX gearbox (Engine/Gears grows with SDK physics_profile MAX_GEARS) and drive layout.
    box = fwd if pilot or len(fwd) == 5 else _geometric(fwd[0], fwd[-1], 5)
    values['Engine/Gear0'] = round(rec['gears_reverse'], 3)
    values['Engine/Gear1'] = 0.0
    for i, g in enumerate(box):
        values['Engine/Gear%d' % (i + 2)] = round(g, 3)
    if pilot:
        n = len(box) + 2
        values['Engine/Gears'] = n
        # retail Megane shift points (% of rev limit): R 75/25, N 35/55, forward 75, 84, then 88..90 up / 55 down
        up = [75., 35., 75., 84.] + [88.] * max(0, n - 7) + [90.] * min(3, n - 4)
        for i in range(n):
            values['Engine/ChangeUpRevs%d' % i] = up[i]
            values['Engine/ChangeDownRevs%d' % i] = 25. if i == 0 else 55.
        # 0043C350: DriveType 0 -> 4WD, 2 -> front axle only (FrontLSDBias), 1 -> rear axle only
        values['Engine/DriveType'] = {'4WD': 0, 'FWD': 2, 'RWD': 1}[layout]
    values['Engine/GearRatioDiff'] = round(rec['final_drive'][DEFAULT_FINAL_DRIVE] * wheel_radius / rec['wheel_radius'], 3)
    # retail Megane points at the test tyre "FrontTest"/"RearTest", which has no Vehicles/Tyres rows;
    # RCX cars take the standard MR rally tyre (harddirt, used by most retail cars)
    values['Suspension/Front/TyreType'] = values['Suspension/Rear/TyreType'] = 'harddirt'
    physics['notes'] += (' RCX PC car table (Rally.exe record %d "%s"): mass %g kg, torque curve x TorqueBoost %.2f '
                         '(peak %.0f), redline %g, idle %g, forward gears %s, final drive %.2f (wheel %.3f -> model %.3f). '
                         'Drive layout %s (TorqueSplit %.2f) %s.'
                         % (rec['record'], rec['name'], rec['mass'], rec['torque_boost'], peak, redline, rec['idle'],
                            [round(g, 3) for g in fwd], rec['final_drive'][DEFAULT_FINAL_DRIVE], rec['wheel_radius'],
                            wheel_radius, layout, split,
                            'applied with the full RCX gearbox (DRIVE1 pilot)' if pilot else
                            'not applied: MR DriveType stays the donor value'))
    return physics


# RCX engine loops (Data/Sound/cars/<folder>/<FOLDER>_4000_1_EXT.wav, 22.05 kHz PCM16 mono): the 4000 rpm
# on-throttle exterior sample of the car's sound folder. RCX has no Citroen folder (Saxo sound code "citr"); the Saxo
# takes the Peugeot 106 (peu) loop of the same 1600 16v class. Focus and Puma share the Ford folder. One waveform
# drives MR's native engine synthesizer (wsDsFxRevs) with the donor's tuning.
ENGINE_SOUNDS = {'IMPREZA00': 'sub', 'ASTRA': 'vaux', 'SAXO': 'peu', 'MINI': 'mini', 'PUMA': 'ford', 'FOCUS': 'ford',
                 'EVO6': 'evo', 'P206': 'peug', 'QUATTRO': 'audi'}
RCX_SOUND_ROOT = 'E:/RallyWorkshop_Sources/sources/Rally Championship Xtreme/Data/Sound/cars'
AUTHOR_SLOT_ID = 27          # author projects build in slot 27; the roster builder rebinds the profile to the final ID
# MR retail engine samples (DataAudio/vehicles/engine*.wav, rev9.wav) have RMS 11-14k, the RCX loops 8-10k:
# owner test 2026-11-16 "quieter than the MR cars". The loop is DC-free, scaled to ENGINE_RMS and its peaks above
# KNEE soft-limited (tanh), so nothing clips.
ENGINE_RMS, KNEE = 12500., 24000.


def louder_engine(samples, rms=ENGINE_RMS, knee=KNEE):
    import math
    dc = sum(samples) / len(samples); x = [v - dc for v in samples]
    g = rms / math.sqrt(sum(v * v for v in x) / len(x))
    out = []
    for v in x:
        a = abs(v * g)
        if a > knee: a = knee + (32767 - knee) * math.tanh((a - knee) / (32767 - knee))
        out.append(int(round(math.copysign(a, v))))
    return out


# AUDIO-RALLY1 phase A: the lift-off one-shot of each car, played by the SDK 'bov_release' layer (native SFX, fired
# on a fast load release while the estimated boost and the RPM are high). WRC = the family's anti-lag crackle,
# Quattro = the turbo dump valve, kit cars and Mini = the generic exhaust pops. (file under Data/Sound, response)
# Owner test 2026-11-18: not heard. The native layer plays at gain x estimated boost (0.3-0.6 for these cars) and the
# native SFX volume curve is steep (0.16 -> -34 dB, 0.3 -> -18 dB, 0.5 -> -10 dB), so gain is 1 and the boost gate
# low; the sources are scaled to the engine loop level (LIFT_RMS, soft-limited like the engine).
LIFT_RMS = 12500
# Owner 2026-11-18: pops also on neutral blips; the native layer skips the limiter cut (omega >= .95 rev limit).
_ANTILAG = {'release_rate_threshold': 2.0, 'boost_threshold': .2, 'gain': 1.0, 'pitch_variation': .1,
            'retrigger_seconds': .35, 'release_decay_seconds': .2, 'min_rpm': 3000, 'mute_neutral': False}
_POPS = {'release_rate_threshold': 2.0, 'boost_threshold': .25, 'gain': 1.0, 'pitch_variation': .12,
         'retrigger_seconds': .6, 'release_decay_seconds': .2, 'min_rpm': 3000, 'mute_neutral': False}
LIFT_SOUNDS = {'IMPREZA00': ('cars/sub/antilag2_ext.wav', _ANTILAG), 'FOCUS': ('cars/ford/antilag3_ext.wav', _ANTILAG),
               'EVO6': ('cars/evo/antilag1_ext.wav', _ANTILAG), 'P206': ('cars/peug/antilag4_ext.wav', _ANTILAG),
               'QUATTRO': ('Car/turbo1.wav', dict(_ANTILAG, boost_threshold=.3, pitch_variation=.06,
                                                   retrigger_seconds=.8)),
               'ASTRA': ('Car/pops.wav', _POPS), 'SAXO': ('Car/pops.wav', _POPS), 'PUMA': ('Car/pops.wav', _POPS),
               'MINI': ('Car/pops.wav', dict(_POPS, gain=.8, boost_threshold=.3, retrigger_seconds=1.0))}


def _lift_layer(author, car, sound_root):
    import hashlib, struct, wave
    from pathlib import Path
    if car not in LIFT_SOUNDS: return None
    rel, response = LIFT_SOUNDS[car]
    folder = Path(sound_root).parent
    src = folder
    for part in rel.split('/'):                     # case-insensitive walk (RCX mixes case)
        src = next(p for p in src.iterdir() if p.name.lower() == part.lower())
    with wave.open(str(src)) as w:
        rate, frames, raw = w.getframerate(), w.getnframes(), w.readframes(w.getnframes())
        assert w.getnchannels() == 1 and w.getsampwidth() == 2
    pcm = louder_engine(list(struct.unpack('<%dh' % frames, raw)), rms=LIFT_RMS)
    dst = Path(author) / 'audio' / 'lift_release.wav'; dst.parent.mkdir(exist_ok=True)
    with wave.open(str(dst), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(struct.pack('<%dh' % frames, *pcm))
    return {'source': {'source_path': 'audio/lift_release.wav', 'source_sha256': hashlib.sha256(dst.read_bytes()).hexdigest(),
                       'trim_frames': [0, frames], 'gain_db': -1.5, 'remove_dc': False, 'crossfade_frames': 0},
            'response': dict(response),
            'provenance': 'Rally Championship Xtreme (PC) Data/Sound/%s, whole file, DC removed, RMS 12500 soft-limited, -1.5 dB resampling headroom; lift-off one-shot '
                          '(AUDIO-RALLY1 phase A, a placeholder until a common rally sound style is chosen).' % rel}


# AUDIO-RALLY1 turbo set (owner 2026-11-18: full turbo effects, one style across cars): the turbo cars take the
# Lancer Evo IV layers (GT4 / GT3 sources, roster evo-class-01) - spool whistle loop for every turbo car, the straight-cut
# gearbox whine for the WRC cars. Their lift-off one-shot stays the RCX anti-lag / dump valve above.
GT_LAYER_ROOT = ('D:/Game/Master Rallye/master-rallye-re-v-cap/.research-output/vehicles/evo-class-01/base-runtime/'
                 'resource-root/DataAudio/vehicles/sdk/lancer_evo4')
TURBO_SPOOL = {'reference_rpm': 4000, 'pitch_min': .35, 'pitch_max': 1.8, 'gain': .8, 'fade_in_rpm': 1500, 'load_threshold': .15,
               'spool_up_seconds': .35, 'spool_down_seconds': .55, 'mute_neutral': False}
GEAR_WHINE = {'reference_rpm': 4000, 'pitch_min': .2, 'pitch_max': 1.8, 'gain_drive': .6, 'gain_coast': .35, 'fade_in_rpm': 1000,
              'mute_neutral': True}
TURBO_CARS = {'IMPREZA00', 'FOCUS', 'EVO6', 'P206', 'QUATTRO'}
WHINE_CARS = {'IMPREZA00', 'FOCUS', 'EVO6', 'P206'}
_GT_PROVENANCE = {'turbo_spool': 'GT4 sound_gt/sound/gt4race2.ins :: 11 (Lancer Evo IV roster layer, 48 kHz canonical)',
                  'transmission_whine': 'GT4 sound_gt/sound/gt4race2.ins :: 12 (Lancer Evo IV roster layer, 48 kHz canonical)'}


def _gt_layer(author, layer, response):
    import hashlib, wave
    from pathlib import Path
    src = Path(GT_LAYER_ROOT) / (layer + '.wav')
    dst = Path(author) / 'audio' / (layer + '.wav'); dst.parent.mkdir(exist_ok=True); dst.write_bytes(src.read_bytes())
    with wave.open(str(dst)) as w: frames = w.getnframes()
    return {'source': {'source_path': 'audio/%s.wav' % layer, 'source_sha256': hashlib.sha256(dst.read_bytes()).hexdigest(),
                       'trim_frames': [0, frames], 'gain_db': 0, 'remove_dc': False, 'crossfade_frames': 0},
            'response': dict(response),
            'provenance': 'Private source adaptation: %s; shared turbo style of the roster (AUDIO-RALLY1).' % _GT_PROVENANCE[layer]}


def add_engine_audio(author, car, sound_root=RCX_SOUND_ROOT):
    """audio-profile.json + pinned audio/engine.wav (SDK addon_sdk/audio_profile.py schema)."""
    import hashlib, json, struct, wave
    from pathlib import Path
    folder = Path(sound_root) / ENGINE_SOUNDS[car]
    src = next(p for p in folder.iterdir() if p.name.lower() == ENGINE_SOUNDS[car] + '_4000_1_ext.wav')
    with wave.open(str(src)) as w:
        rate, frames, raw = w.getframerate(), w.getnframes(), w.readframes(w.getnframes())
        assert w.getnchannels() == 1 and w.getsampwidth() == 2
    pcm = louder_engine(list(struct.unpack('<%dh' % frames, raw)))
    author = Path(author); dst = author / 'audio' / 'engine.wav'; dst.parent.mkdir(exist_ok=True)
    with wave.open(str(dst), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(struct.pack('<%dh' % frames, *pcm))
    profile = {'audio_profile_version': 1, 'policy': 'native_custom_engine', 'physical_car_id': AUTHOR_SLOT_ID,
               'stock_audio_profile_id': base.VEHICLES[car]['audio'], 'namespace': 'rcx_' + car.lower(),
               'engine': {'source_path': 'audio/engine.wav', 'source_sha256': hashlib.sha256(dst.read_bytes()).hexdigest(),
                          'trim_frames': [0, frames], 'gain_db': 0, 'remove_dc': False, 'crossfade_frames': 0},
               'notes': 'Rally Championship Xtreme (PC) Data/Sound/cars/%s/%s: 4000 rpm on-throttle exterior loop, whole '
                        'file, DC removed, RMS %d with soft-limited peaks (MR engine level); one waveform through the '
                        'native MR engine synthesizer with the donor tuning.' % (folder.name, src.name, ENGINE_RMS)}
    lift = _lift_layer(author, car, sound_root)
    if lift: profile['bov_release'] = lift
    if car in TURBO_CARS: profile['turbo_spool'] = _gt_layer(author, 'turbo_spool', TURBO_SPOOL)
    if car in WHINE_CARS: profile['transmission_whine'] = _gt_layer(author, 'transmission_whine', GEAR_WHINE)
    (author / 'audio-profile.json').write_text(json.dumps(profile, indent=1), encoding='utf-8')
    return profile


def create_pilot(scene_path, car, retail_sma, retail_root, output, **kw):
    import json
    from pathlib import Path
    summary = base.create_pilot(scene_path, car, retail_sma, retail_root, output, **kw)
    path = Path(summary['author']) / 'physics-profile.json'
    physics = balance_physics(json.loads(path.read_text()), car, summary['dimensions']['wheel_radius'])
    path.write_text(json.dumps(physics, indent=2) + chr(10))
    summary['engine_audio'] = add_engine_audio(summary['author'], car)['namespace']
    summary['physics_balance'] = {k: v for k, v in physics['overrides'][next(iter(physics['overrides']))].items()
                                  if k in ('Chassis/TotalMass', 'Engine/PeakTorque', 'Engine/GearRatioDiff')}
    return summary
