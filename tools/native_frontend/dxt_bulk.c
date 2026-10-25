/* Canonical loose-file MR cached texture decoding: same BGRA bytes, native
   image ownership and GPU path, one contiguous read instead of one per pixel.
   Unknown stream implementations and noncanonical layouts use original code. */
typedef unsigned int U;
typedef unsigned char B;
typedef void * (__cdecl *Alloc)(U);
typedef void (__cdecl *Free)(void *);
typedef U (__thiscall *Query)(U *);
typedef B (__thiscall *Read)(U *,void *,U);
typedef B (__thiscall *Seek)(U *,U);
typedef U * (__thiscall *ImageCtor)(U *,U,U);
typedef void (__thiscall *Delete)(U *,U);
typedef void * (__stdcall *Original)(U *);
static void dispose(U *image) { ((Delete)(*(U**)image)[0])(image,1); }
extern "C" void * __stdcall dxt_bulk(U *stream) {
 U position,length,dimensions[2],width,height,bytes; U *image,*result,*vt;
 if(!stream || stream[0]!=0x69ce44 || ((B*)stream)[0x10] || stream[3]==0xffffffff)
  return ((Original)0x581120)(stream);
 vt=(U*)stream[0];position=((Query)vt[5])(stream);
 if(position!=12)return ((Original)0x581120)(stream);
 length=((Query)vt[6])(stream);
 if(length<20)return ((Original)0x581120)(stream);
 if(!((Read)vt[9])(stream,dimensions,8))return 0;
 width=dimensions[0];height=dimensions[1];
 if(!width||!height||width>4096||height>4096 || width*height*4!=length-20){
  if(!((Seek)vt[11])(stream,position))return 0;
  return ((Original)0x581120)(stream);
 }
 bytes=width*height*4;
 image=(U*)((Alloc)0x5c1cb4)(0x14);
 if(!image)return 0;
 ((ImageCtor)0x5ff230)(image,width,height);
 if(!image[2] || !((Read)vt[9])(stream,(void*)image[2],bytes)) {dispose(image);return 0;}
 result=(U*)((Alloc)0x5c1cb4)(4);
 if(!result){dispose(image);return 0;}
 *result=(U)image;
 return result;
}
