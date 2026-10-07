"""Ignored PSB atlas/assembly diagnostic images; no game-screen compositor.

Rasters use raw GXI scanline order and PSB local Y increasing down. Raw GXI
row 0 corresponds to PSB V=1: crop rows are (1-vmax)*H .. (1-vmin)*H. UV
bounds select sampled pixels, not the padded allocation rectangle. This
convention is visually corroborated, not a replay of the PS2 render pipeline.
"""
import argparse
from pathlib import Path
import psbtool as p


def assemble(image, texture_bytes):
    from PIL import Image
    box = image['local_bounds_xyxy']
    if box is None: return Image.new('RGBA',(1,1))
    width,height = box[2]-box[0],box[3]-box[1]
    if not 0<width<=2048 or not 0<height<=2048:
        raise p.FormatError('Diagnostic canvas outside bounds')
    result = Image.new('RGBA',(width,height))
    covered = {i for q in image['quads'] for i in q['triangle_indices']}
    if any(r['texture_name']!='Null' and r['index'] not in covered for r in image['triangles']):
        raise p.FormatError('Diagnostic assembly requires proven rectangular triangle pairs')
    for quad in image['quads']:
        raw = texture_bytes[quad['texture_name']]
        gxi = p.parse_gxi(raw)
        atlas = Image.frombytes('RGBA',(gxi['width'],gxi['height']),raw[8:])
        uv = quad['uv_bounds']
        pixels = [uv[0]*gxi['width'],(1-uv[3])*gxi['height'],
                  uv[2]*gxi['width'],(1-uv[1])*gxi['height']]
        rect = list(map(round,pixels))
        if any(abs(rect[i]-pixels[i])>1e-6 for i in range(4)):
            raise p.FormatError('Diagnostic requires integer UV pixel boundaries')
        x0,y0,x1,y1 = quad['local_bounds_xyxy']
        patch = atlas.crop(rect).resize((x1-x0,y1-y0),Image.Resampling.NEAREST)
        result.alpha_composite(patch,(x0-box[0],y0-box[1]))
    return result


def main():
    from PIL import Image,ImageDraw
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('psb',type=Path)
    ap.add_argument('--texture-dir',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,required=True)
    a = ap.parse_args()
    if not a.output_dir.resolve().is_relative_to((Path(__file__).resolve().parents[1]/'data').resolve()):
        raise p.FormatError('Diagnostic images must remain in ignored ps2-research/data')
    doc = p.parse_psb(a.psb.read_bytes())
    textures = {n:(a.texture_dir/(n.upper()+'.GXI')).read_bytes() for n in doc['texture_references']}
    p.verify(doc,textures)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    columns,cell_w,cell_h = 6,220,210
    sheet = Image.new('RGB',(columns*cell_w,cell_h*((len(doc['images'])+columns-1)//columns)),(44,44,44))
    drawing = ImageDraw.Draw(sheet)
    records = []
    for i,image in enumerate(doc['images']):
        rendered = assemble(image,textures)
        path = a.output_dir/f'image-{i:03d}.png'
        rendered.save(path)
        x,y = (i%columns)*cell_w,(i//columns)*cell_h
        rendered.thumbnail((200,170),Image.Resampling.NEAREST)
        sheet.paste(rendered,(x+8,y+30),rendered)
        keys = [r['key_u32'] for r in doc['mappings'] if r['image_index_u32']==i]
        drawing.text((x+8,y+6),f'image {i}; keys '+','.join(map(str,keys)),fill='white')
        records.append({'image_index':i,'keys':keys,'local_bounds':image['local_bounds_xyxy'],
                        'output':path.name,'evidence':'CONFIRMED_BY_VISUAL_RECONSTRUCTION'})
    sheet.save(a.output_dir/'contact.png')
    p.write_json(a.output_dir/'provenance.json',{'source':doc['provenance'],'method':__doc__, 'images':records})


if __name__=='__main__':
    main()
