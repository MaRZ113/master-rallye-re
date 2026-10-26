"""Per-addon HUD tint values and a display-only shared-image multiplication."""
import math,re,struct

PRESETS={'Amber':'#E8B257','Cyan':'#20D9E8','Red':'#E83838','Green':'#48CC70','White':'#FFFFFF'}


def normalized_rgb(value):
    if isinstance(value,str):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',value):raise ValueError('Marker HEX must be #RRGGBB')
        return [int(value[i:i+2],16)/255 for i in (1,3,5)]
    if not isinstance(value,(list,tuple))or len(value)!=3 or any(type(v)not in (float,int)or not math.isfinite(v)or not 0<=v<=1 for v in value):raise ValueError('Marker RGB requires three finite normalized values')
    return list(value)


def colour_info(rgba):
    if not isinstance(rgba,list)or len(rgba)!=4:raise ValueError('Marker requires normalized RGBA')
    rgb=normalized_rgb(rgba[:3]);alpha=rgba[3]
    if type(alpha)not in (int,float)or not math.isfinite(alpha)or not 0<=alpha<=1:raise ValueError('Invalid original marker alpha')
    return {'rgba':[*rgb,alpha],'hex':'#'+''.join(f'{round(v*255):02X}'for v in rgb),'f32le_hex':struct.pack('<4f',*rgba).hex()}


def tinted_marker(image,rgba):
    """Native diffuse tint approximation; no resource or alpha writes."""
    from PIL import Image
    colour_info(rgba)
    source=image.convert('RGBA');channels=source.split()
    return Image.merge('RGBA',[channels[i].point(lambda p,g=rgba[i]:round(p*g))for i in range(3)]+[channels[3]])
