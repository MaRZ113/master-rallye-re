"""Original GT3 GT2K car-color associations, without tint synthesis.

Header spans and key/ID joins are checked against the supplied database bytes.
Color IDs and list order are preserved; render palette indices need a separate
ModelSet1 count/provenance check. Thumbnail RGB is descriptive, never applied.
"""
import struct
from .gt3_source import Reader,sha

def names(raw):
    r=Reader(raw)
    if r.span(0,4)!=b'STDB':raise ValueError('GT3 colour names require STDB')
    count,encoding,reserved,size=r.unpack('<IhhI',4)
    if size!=len(raw)or reserved or encoding not in (1,2,-1)or count>100000:raise ValueError('GT3 colour STDB header')
    offsets=r.unpack('<'+'I'*count,16);out=[]
    for at in offsets:
        if at<16+count*4:raise ValueError('GT3 colour string overlaps table')
        n=r.unpack('<H',at)[0];b=r.span(at+2,n)
        out.append(b.decode('utf-16le').rstrip('\0')if encoding==2 else b.decode('ascii','backslashreplace').rstrip('\0'))
    return out

def catalog(raw,strings):
    r=Reader(raw)
    if r.span(0,4)!=b'GT2K':raise ValueError('GT3 colour catalog requires GT2K')
    reserved,count,lists,colors,size=r.unpack('<5I',4)
    if reserved or not 0<count<=4096 or size!=len(raw)or not 24+16*count<=lists<=colors<len(raw):raise ValueError('GT3 colour header spans')
    labels=names(strings);n=r.u32(colors)
    if not 0<n<=65536 or colors+4+16*n!=size:raise ValueError('GT3 colour record span')
    palette={}
    for i in range(n):
        at=colors+4+i*16;key,latin,jp,thumbnail=r.unpack('<4I',at)
        if key in palette or max(latin,jp)>=len(labels):raise ValueError('GT3 colour ID/string ambiguity')
        palette[key]={'colour_id':key,'latin_name':labels[latin],'japanese_name_raw':labels[jp],'thumbnail_word':thumbnail,'record_offset':at,'record_sha256':sha(r.span(at,16))}
    models={}
    for i in range(count):
        at=24+i*16;key,n,relative=r.unpack('<QII',at);start=lists+relative
        if key in models or not 0<n<=256 or not lists<=start<=start+4*n<=colors:raise ValueError('GT3 model colour list span/identity')
        ids=r.unpack('<'+'I'*n,start)
        if len(set(ids))!=n or any(k not in palette for k in ids):raise ValueError('GT3 unresolved/duplicate source colour ID')
        models[key]={'model_key':hex(key),'record_offset':at,'indices_offset':start,'source_colourways':[{'source_index':j,**palette[k]}for j,k in enumerate(ids)]}
    return {'models':models,'source_sha256':sha(raw),'strings_sha256':sha(strings),'boundary':'Original ordered color-ID associations; thumbnail words are not recoloring recipes. Match ModelSet palette count before build.'}

def select(source,model_key,index,modelset):
    if model_key not in source['models']:raise ValueError('source model has no colour catalog entry')
    colours=source['models'][model_key]['source_colourways']
    if len(colours)!=modelset['source_colourway_count']:raise ValueError('source database/ModelSet colourway count mismatch')
    if type(index)is not int or not 0<=index<len(colours):raise ValueError('source colourway selection outside catalog')
    if any(t['source_clut_variants'] and index>=len(t['source_clut_variants'])for t in modelset['texture_sets'])or modelset['material_variants']and index>=len(modelset['material_variants']):raise ValueError('source colourway variant tables incomplete')
    return {**colours[index],'catalog_sha256':source['source_sha256'],'strings_sha256':source['strings_sha256'],'clut_sets':[t['source_clut_variants'][index]if t['source_clut_variants']else None for t in modelset['texture_sets']],'material_variant':modelset['material_variants'][index]if modelset['material_variants']else None,'policy':'immutable source palette/material selection; no RGB tint; custom paint remains a separate layer'}
