"""Explicit, hash-pinned paint masks. No semantic inference from image colours.

Rows use the existing PNG export convention. Mask zero and source alpha are
invariant; a mask is an owner's qualification, not a claim of automatic parsing.
"""
import hashlib
import io
from .dxt import parse_dxt_bytes

COLOR_PRESETS = {'Rally red': [190, 28, 32], 'Amber': [210, 143, 40],
                 'Forest green': [35, 100, 65], 'Midnight blue': [30, 55, 110],
                 'Ivory': [225, 220, 205]}


def masked_paint(raw, mask_png, color, *, source_sha256, evidence):
    if hashlib.sha256(raw).hexdigest() != source_sha256:
        raise ValueError('Paint source SHA256 mismatch')
    if not isinstance(evidence, str) or len(evidence.strip()) < 12:
        raise ValueError('Describe the qualified paint region and protected content')
    if len(color) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in color):
        raise ValueError('Paint color requires three byte values')
    from PIL import Image
    t = parse_dxt_bytes(raw)
    with Image.open(io.BytesIO(mask_png)) as image:
        w,h=image.size
        if image.format!='PNG' or (w,h)!=(t.width,t.height) or w*h>16*1024*1024:raise ValueError('Paint mask must be a bounded exact-size PNG')
        rgba=image.convert('RGBA').tobytes()
    if (w, h) != (t.width, t.height):
        raise ValueError('Paint mask must have exact exported texture dimensions')
    # A greyscale opaque mask avoids ambiguous alpha-versus-luminance ownership.
    if any(rgba[i] != rgba[i+1] or rgba[i] != rgba[i+2] or rgba[i+3] != 255 for i in range(0,len(rgba),4)):
        raise ValueError('Use an opaque greyscale PNG mask: white paint, black protected')
    weights = rgba[::4]
    if not any(weights):raise ValueError('Empty paint mask')
    # Source native BGRA rows are vertically inverted by the established exporter.
    out = bytearray(t.bgra); changed = 0; protected = 0; visible_alpha = 0
    for y in range(h):
        for x in range(w):
            weight = weights[y*w+x]; i=((h-1-y)*w+x)*4
            if not weight:protected += 1;continue
            visible_alpha += t.bgra[i+3] > 0
            # Luminance-preserving tint: retain local baked lighting/detail.
            b,g,r = t.bgra[i:i+3]; light=(.2126*r+.7152*g+.0722*b)/255
            for c,v in enumerate(reversed(color)):
                out[i+c]=round((t.bgra[i+c]*(255-weight)+v*light*weight)/255)
            changed += out[i:i+3] != t.bgra[i:i+3]
    import zlib,struct
    pixels=bytes(out); result=t.header[:8]+struct.pack('<I',zlib.crc32(pixels)&0xffffffff)+t.header[12:]+pixels
    parse_dxt_bytes(result)
    return result, {'changed_texels':changed,'protected_texels':protected,'nonzero_alpha_selected_texels':visible_alpha,'alpha_preserved':pixels[3::4]==t.bgra[3::4],
                    'mask_sha256':hashlib.sha256(mask_png).hexdigest(),'evidence':evidence,
                    'algorithm':'source luminance tint within explicit PNG mask; no automatic logo detection'}
