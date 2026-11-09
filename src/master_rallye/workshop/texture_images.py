"""Image-file normalization at the UI boundary; FEED codec stays unchanged."""
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps

IMPORT_FORMATS={'PNG','JPEG','BMP','WEBP','GIF','TGA','TIFF'}
IMPORT_FILTER='Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif *.tga *.tif *.tiff)'
EXPORT_FILTER='PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;WebP (*.webp)'


def load_image(path):
    path=Path(path)
    if path.stat().st_size>64*1024*1024:raise ValueError('Image exceeds 64 MiB import budget')
    warnings=[]
    with Image.open(path) as image:
        if image.format not in IMPORT_FORMATS:raise ValueError('Unsupported image format')
        if image.width*image.height>16*1024*1024:raise ValueError('Image exceeds 16 megapixel budget')
        if getattr(image,'n_frames',1)>1:warnings.append('Animated image: only frame 0 was imported')
        image.seek(0)
        # Apply file orientation to pixels, never to UVs or native resource rows.
        if image.getexif().get(274,1)!=1:warnings.append('EXIF orientation applied to imported image')
        rgba=ImageOps.exif_transpose(image).convert('RGBA')
        return rgba.width,rgba.height,rgba.tobytes(),warnings


def rgba_png(width,height,pixels):
    out=BytesIO();Image.frombytes('RGBA',(width,height),pixels).save(out,format='PNG');return out.getvalue()


def export_image(png,path):
    path=Path(path);suffix=path.suffix.lower();warnings=[]
    if suffix=='.png':path.write_bytes(png);return warnings
    formats={'.jpg':'JPEG','.jpeg':'JPEG','.bmp':'BMP','.webp':'WEBP'}
    if suffix not in formats:raise ValueError('Export extension must be PNG/JPEG/BMP/WebP')
    image=Image.open(BytesIO(png)).convert('RGBA')
    if suffix in ('.jpg','.jpeg','.bmp'):
        warnings.append('JPEG/BMP export has no alpha; composited on white')
        background=Image.new('RGBA',image.size,'white');background.alpha_composite(image);image=background.convert('RGB')
    image.save(path,format=formats[suffix],**({'lossless':True} if suffix=='.webp' else {'quality':95} if suffix in ('.jpg','.jpeg') else {}))
    return warnings
