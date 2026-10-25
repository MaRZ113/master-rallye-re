"""Optional measured MR preview presentation; no proprietary images required.

Camera angles and lighting are authoring approximations, not recovered source
camera settings. Pixel bounds/tone targets are measured from the retail corpus.
"""
import math
from .manifest import AddonValidationError

PROFILES={
 'vehicle_select_art':{'size':(128,128),'area':(12,65,104,123),'baseline':121,'p90':166.,'camera':(138.,10.),'distance':7.,'ambient':.52,'key':.65},
 'smallcarsheet':{'size':(32,16),'area':(0,0,32,15),'baseline':15,'p90':203.,'camera':(-90.,0.),'distance':None,'ambient':.70,'key':.55},
}

def compose_preview(image,role):
    """Role-specific tone, premultiplied reduction and grounded composition.

    Source viewpoint cannot be reconstructed from a single supplied PNG. Use
    the optional model renderer to obtain the profile's authored camera.
    """
    from .ui_assets import fit_rgba,alpha_bounds
    if role not in PROFILES:raise AddonValidationError('unknown preview role')
    profile=PROFILES[role];w,h,px=image
    if not 0<w<=4096 or not 0<h<=4096 or len(px)!=4*w*h:raise AddonValidationError('invalid preview input')
    luminance=sorted(.2126*px[i]+.7152*px[i+1]+.0722*px[i+2] for i in range(0,len(px),4) if px[i+3]>200)
    if not luminance:raise AddonValidationError('preview requires an opaque vehicle silhouette')
    p90=luminance[int(.9*(len(luminance)-1))]
    # Bounded exposure retains vehicle/livery differences. Do not histogram
    # match every car to the same average brightness or recolour the livery.
    exposure=max(.8,min(1.6,profile['p90']/max(1.,p90)));edited=bytearray(px)
    for i in range(0,len(px),4):
        for k in range(3):
            value=px[i+k]*exposure
            # Gentle shoulder retains highlights instead of hard white clipping.
            edited[i+k]=round(value if value<=220 else 220+35*(1-math.exp(-(value-220)/35)))
    width,height=profile['size'];rgba=fit_rgba((w,h,bytes(edited)),width,height,padding=1 if role=='vehicle_select_art' else 0,target_bounds=profile['area'])
    bounds=alpha_bounds((width,height,rgba));shift=profile['baseline']-bounds[3]
    if bounds[1]+shift<profile['area'][1]:shift=profile['area'][1]-bounds[1]
    out=bytearray(len(rgba))
    for y in range(height):
        dest=y+shift
        if 0<=dest<height:out[dest*width*4:(dest+1)*width*4]=rgba[y*width*4:(y+1)*width*4]
    final=bytes(out)
    return final,{'profile':'mr-native-v1','role':role,'source_p90':p90,'exposure':exposure,'target_p90':profile['p90'],
        'bounds':list(alpha_bounds((width,height,final))),'baseline':profile['baseline'],'viewpoint_policy':'model renderer profile or caller-provided PNG viewpoint; no 2D camera reconstruction','filter':'premultiplied area; no sharpening halos'}
