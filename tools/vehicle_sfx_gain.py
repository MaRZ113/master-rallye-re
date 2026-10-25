"""Original MR 005A8300 SFX gain curve, for nonspatial audition.

This is the near-listener, single-listener SetVolume curve from exact retail
SHA256 bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4.
It is not engine grain DSP, DirectSound device emulation, distance attenuation,
multiple-listener mixing, speaker response or proof of audible runtime playback.
FISTP is modeled with normal x87 nearest-even rounding. The process changing its
x87 rounding control can change half-unit boundaries; that mode is not inferred.
"""
import math
import struct


def _f32(value):
    return struct.unpack('<f',struct.pack('<f',value))[0]


def sfx_volume_hundredth_db(gain):
    """Native SetVolume units; gain is a finite authored scalar, clamped 0..1.

    Source SFX gain is float32; the backend spills the piecewise result to
    float32 before FISTP. Below float32(.05), native code forces -10000.
    """
    if isinstance(gain,bool) or not isinstance(gain,(int,float)) or not math.isfinite(gain):
        raise ValueError('SFX gain must be a finite number')
    x=_f32(max(0.,min(1.,gain)))
    if x<_f32(.05):return -10000
    if x<.125:y=x*8*6000-10000
    elif x<.25:y=(x-.125)*8*2000-4000
    elif x<.5:y=(x-.25)*4*1000-2000
    elif x<.75:y=(x-.5)*4*500-1000
    else:y=(x-.75)*4*500-500
    return round(_f32(y))


def sfx_near_amplitude(gain):
    """Convert the native dB command to a PCM amplitude factor for audition.

    -10000 is treated as silence, matching the native sub-.05 cutoff intention.
    Other values use the standard dB amplitude relation, 10**(dB/20).
    """
    volume=sfx_volume_hundredth_db(gain)
    return 0. if volume<=-10000 else 10.**(volume/2000.)


EVIDENCE={
    'function':'005A8300',
    'gain_branches':'005A842E..005A8574',
    'set_volume_call':'005A85AF',
    'constants':{
        '0068F5E8':'cdcc4c3d', # float32 .05
        '00690DE4':'0000403f', # .75
        '0068F958':'0000003f', # .5
        '0068FEAC':'0000803e', # .25
        '0068F964':'0000003e', # .125
        '0068FEF4':'00008040', # 4
        '00691070':'0000fa43', # 500
        '00690B38':'00007a44', # 1000
        '00690C48':'0000fa44', # 2000
        '00692D60':'00007a45', # 4000
        '0068F968':'00000041', # 8
        '00692D5C':'0080bb45', # 6000
        '00692770':'00401c46', # 10000
    },
}
