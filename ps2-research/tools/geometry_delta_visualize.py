"""Ignored source-coordinate SVG diagnostics. No runtime visibility claim."""
from pathlib import Path
import html
import geometry_delta as g

COLORS={'EXACT_TRIANGLE_MATCH':'#566574','SAME_SURFACE_DIFFERENT_TRIANGULATION':'#61d4b3',
        'PARTIAL_SURFACE_OVERLAP':'#efa456','GEOMETRY_MODIFIED':'#bb85df',
        'PS2_EXTRA_VISUAL_SOURCE':'#55b7ee','PC_EXTRA_COMPILED_DRAW':'#f16e76',
        'AMBIGUOUS':'#f5da70','DIAGNOSTIC_DEGENERATE':'#888888'}


def write_svg(path,a,b,forward,reverse,course):
    path=g.local_output(Path(path));path.parent.mkdir(parents=True,exist_ok=True)
    box=g.bounds(a.positions+b.positions);lo,hi=box['min'],box['max']
    scale=1000/max(hi[0]-lo[0],hi[2]-lo[2],1.)
    height=200+(hi[2]-lo[2])*scale
    def pts(tri):
        return ' '.join('%.3f,%.3f'%(50+(p[0]-lo[0])*scale,160+(hi[2]-p[2])*scale) for p in tri)
    lookup={f.identifier:f for f in a.faces+b.faces}
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="%g" viewBox="0 0 1120 %g">'%(height,height),
           '<rect width="100%" height="100%" fill="#111b24"/>',
           '<g fill="white" font-family="sans-serif" font-size="16">',
           '<text x="30" y="27">%s — GEOM1 authored source geometry</text>'%html.escape(course),
           '<text x="30" y="51">Game X right, Z up. No live LOD, instance-pose or render-state proof.</text></g>']
    for k,(label,color) in enumerate(COLORS.items()):
        parts.append('<text x="%d" y="%d" fill="%s" font-family="sans-serif" font-size="12">%s</text>'%
                     (30+(k%3)*365,78+(k//3)*20,color,html.escape(label)))
    # Layer order is diagnostic. PC candidates underneath; PS2 water highlighted
    # separately regardless of whether a relaxed tolerance finds partial overlap.
    rows=reverse+forward
    for relation in COLORS:
        parts.append('<g id="%s" fill="%s" fill-opacity=".45" stroke="%s" stroke-width=".25">'%(relation,COLORS[relation],COLORS[relation]))
        for row in rows:
            if row['geometry_relation']==relation:
                parts.append('<polygon points="%s"><title>%s</title></polygon>'%(pts(lookup[row['source']].points),html.escape(row['source'])))
        parts.append('</g>')
    parts.append('<g id="PS2_WATER_SOURCE" fill="none" stroke="#ffffff" stroke-width="1.2">')
    for f in a.faces:
        if g.w.shader_contract(a.groups[f.group]['material'])['water_mode'] is not None:
            parts.append('<polygon points="%s"/>'%pts(f.points))
    parts.append('</g></svg>')
    path.write_text('\n'.join(parts)+'\n',encoding='utf-8')


def write_png(path,a,b,forward,reverse,course):
    """Optional Pillow scientific preview; original geometry stays ignored."""
    from PIL import Image,ImageDraw,ImageFont
    path=g.local_output(Path(path));path.parent.mkdir(parents=True,exist_ok=True)
    im=Image.new('RGB',(1200,1000),'#111b24');draw=ImageDraw.Draw(im)
    try:font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',17)
    except OSError:font=ImageFont.load_default()
    bb=g.bounds(a.positions+b.positions);lo,hi=bb['min'],bb['max']
    scale=min(1080/max(hi[0]-lo[0],1),760/max(hi[2]-lo[2],1))
    def points(tri):return [(60+(p[0]-lo[0])*scale,210+(hi[2]-p[2])*scale) for p in tri]
    lookup={f.identifier:f for f in a.faces+b.faces}
    for rows in (reverse,forward):
        for row in rows:
            if row['geometry_relation'] not in ('DIAGNOSTIC_DEGENERATE',):
                color=COLORS[row['geometry_relation']]
                draw.polygon(points(lookup[row['source']].points),fill=color)
    for f in a.faces:
        if g.w.shader_contract(a.groups[f.group]['material'])['water_mode'] is not None:
            draw.polygon(points(f.points),fill='#22cfea',outline='#d4ffff')
    draw.text((25,15),course+' | GEOM1 source-geometry delta | X right, Z up',fill='white',font=font)
    draw.text((25,43),'Projection collapses Y. Authored geometry; live LOD and visibility UNKNOWN.',fill='white',font=font)
    for i,(label,color) in enumerate(COLORS.items()):
        x,y=25+(i%2)*585,80+(i//2)*25
        draw.rectangle((x,y+4,x+16,y+18),fill=color)
        draw.text((x+24,y),label,fill='white',font=font)
    draw.text((25,183),'Cyan highlight: original PS2 water/puddle source; not a gameplay frame.',fill='#22cfea',font=font)
    im.save(path)
