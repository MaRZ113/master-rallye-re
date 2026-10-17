import sys, struct
sys.path.insert(0, sys.argv[1]); import gsdump
G=gsdump.GS
orig=G.kick
def kick(self,x,y,z,f):
    orig(self,x,y,z,f); self.kicks[-1]=self.kicks[-1]+(self.r[0x03],)
G.kick=kick
hdr,shot,gs,packets=gsdump.replay(sys.argv[2],frames=1)
first=True
for i,k in enumerate(gs.kicks):
    key=k[0]
    if key[9]==0x1e8:
        uv=k[-1]; u=(uv&0x3fff)/16; v=((uv>>16)&0x3fff)/16
        st=k[6]; s=struct.unpack('<f',struct.pack('<I',st&0xffffffff))[0]; t=struct.unpack('<f',struct.pack('<I',(st>>32)&0xffffffff))[0]
        print(i,'prim',key[0],'attr',hex(key[1]),'tbp',hex(key[3]),'tbw',key[4],'alpha',hex(key[7]),'fix',key[8],'xy',k[3][:2],'uv',(u,v),'st',(round(s,4),round(t,4)),'q',round(k[5],4),'rgba',k[1])
