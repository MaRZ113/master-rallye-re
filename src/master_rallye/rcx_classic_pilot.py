"""Rally Championship Xtreme (PC) cars -> MR Classic native projects.

Same owner policy and pipeline as the TXR3 / Evo pilots (txr3_classic_pilot.create_pilot):
source geometry, source wheels and true dimensions (metres, no rescale, source track),
source diffuse textures with the stock MR material of each semantic role.

Roles come from the RCX part name, texture and QTO material flags:
flags 0x80 on the exterior atlas = painted/reflective panel (MR paint), 0x08 = transparent
(windows), the wheel textures split into tyre (tread, wall) / rim (chrome) / disc (trim).

Classes by power (owner 2026-11-16): A >= 300 bhp, B 260-280, C 200-220, D <= 150.
Physics donor for the pilot: retail MR "megane" (small rally car); the RCX CarStats mapping
is a separate step.
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


# key: family, display name, manufacturer, model, results, power class, bhp, drive
CARS = {
    'IMPREZA00': ('RcxImpreza2000', 'Subaru Impreza WRC 2000', 'SUBARU', 'IMPREZA WRC 2000', 'SUBARU IMPREZA', 'A', 300, '4WD'),
    'ASTRA': ('RcxAstraKitCar', 'Vauxhall Astra Kit Car', 'VAUXHALL', 'ASTRA KIT CAR', 'VAUXHALL ASTRA', 'B', 280, 'FWD'),
    'SAXO': ('RcxSaxo', 'Citroen Saxo', 'CITROEN', 'SAXO', 'CITROEN SAXO', 'C', 215, 'FWD'),
    'MINI': ('RcxMiniCooper', 'Mini Cooper', 'MINI', 'COOPER', 'MINI COOPER', 'D', 115, 'FWD'),
}
ARCHIVES = {'IMPREZA00': 'subaru impreza00.rcx', 'ASTRA': 'Astra.rcx', 'SAXO': 'Citroen Saxo.rcx', 'MINI': 'Mini Cooper.rcx'}

for key, (family, name, make, model, results, cls, bhp, drive) in CARS.items():
    base.VEHICLES[key] = {
        'family': family, 'name': name + ' (RCX)', 'manufacturer': make, 'model': model, 'results': results,
        'donor': 'Megane', 'audio': 18, 'class': 'T2', 'target_class': 'RCX power class ' + cls,
        'power': {'bhp': bhp, 'drive': drive, 'class': cls},
        'label': 'RCX', 'source_label': 'Rally Championship Xtreme (PC)', 'source_format': 'RCX Universal Vehicle Scene',
        'adapter_id': 'rcx-pc/1', 'long_axis': 11, 'role_fn': _role, 'glass_key': 'mat-body-windows-00',
        'keep_source_scale': True, 'source_track': True,
        'brake_evidence': 'RCX brakelight l/r parts (exterior atlas).'}


# RCX masses (kg) from the PS2 CAR_DEFINITION table (SLES_507.63, CarDefs.cpp, dumped by
# research/source-formats rally-championship-ps2/car_definitions.py).
MASS = {'IMPREZA00': 1430., 'ASTRA': 1160., 'SAXO': 1150., 'MINI': 870.}
# Donor reference: retail MR Megane = 350 Nm PeakTorque, GearRatioDiff 3.40, wheel radius 0.38 m,
# taken as a ~260 bhp rally car. Torque scales with the RCX power so power classes stay fair
# (MR is an arcade model: every retail car is DriveType 0, so the RCX drive layout is recorded,
# not applied).
DONOR_TORQUE, DONOR_BHP, DONOR_DIFF, DONOR_WHEEL = 350., 260., 3.40, .38


def balance_physics(physics, key, wheel_radius):
    spec = base.VEHICLES[key]; bhp = spec['power']['bhp']
    values = physics['overrides'][next(iter(physics['overrides']))]
    values['Chassis/TotalMass'] = MASS[key]
    values['Engine/PeakTorque'] = round(DONOR_TORQUE * bhp / DONOR_BHP, 1)
    # same road speed per engine rev as the donor despite the smaller RCX wheel
    values['Engine/GearRatioDiff'] = round(DONOR_DIFF * wheel_radius / DONOR_WHEEL, 3)
    # retail Megane points at the test tyre "FrontTest"/"RearTest", which has no Vehicles/Tyres rows;
    # RCX cars take the standard MR rally tyre (harddirt, used by most retail cars)
    values['Suspension/Front/TyreType'] = values['Suspension/Rear/TyreType'] = 'harddirt'
    physics['notes'] += (' RCX balance: TotalMass = RCX %g kg; PeakTorque = 350 Nm x %d bhp / 260 (power class %s); '
                         'GearRatioDiff scaled by wheel radius %.3f / 0.38. Drive layout %s not applied (MR DriveType 0 for all cars).'
                         % (MASS[key], bhp, spec['power']['class'], wheel_radius, spec['power']['drive']))
    return physics


def create_pilot(scene_path, car, retail_sma, retail_root, output, **kw):
    import json
    from pathlib import Path
    summary = base.create_pilot(scene_path, car, retail_sma, retail_root, output, **kw)
    path = Path(summary['author']) / 'physics-profile.json'
    physics = balance_physics(json.loads(path.read_text()), car, summary['dimensions']['wheel_radius'])
    path.write_text(json.dumps(physics, indent=2) + chr(10))
    summary['physics_balance'] = {k: v for k, v in physics['overrides'][next(iter(physics['overrides']))].items()
                                  if k in ('Chassis/TotalMass', 'Engine/PeakTorque', 'Engine/GearRatioDiff')}
    return summary
