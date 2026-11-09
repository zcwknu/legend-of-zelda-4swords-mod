"""Patch entry.arc so the Two-Player row of the player-count menu
(adv_n_player.blo) shows GameCube controllers instead of Game Boy Advances.
Usage: patch_menu.py <original entry.arc> <output entry.arc>"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rarc import yaz0, rarc
from yaz0enc import yaz0_encode
def blo_info(d,base):
    o=base+0x20; ch={}
    while o<len(d):
        t=bytes(d[o:o+4]); sz=struct.unpack('>I',d[o+4:o+8])[0]
        if t not in ch: ch[t]=o
        if t==b'EXT1' or sz==0: break
        o+=sz
    T=ch[b'TEX1']; tb=T+0x10; tn=struct.unpack('>H',d[tb:tb+2])[0]; tex=[]
    for i in range(tn):
        q=struct.unpack('>H',d[tb+2+2*i:tb+4+2*i])[0]; L=d[tb+q+1]; tex.append(d[tb+q+2:tb+q+2+L].decode())
    M=ch[b'MAT1']; offs=struct.unpack('>20I',d[M+0xc:M+0x5c]); n=struct.unpack('>H',d[M+8:M+10])[0]
    nt=M+offs[2]; names=[]
    for i in range(n):
        h,q=struct.unpack('>HH',d[nt+4+4*i:nt+8+4*i]); names.append(d[nt+q:d.index(b'\0',nt+q)].decode())
    texno_tab=M+offs[11]
    return tex,names,M+offs[0],texno_tab
def patch_blo(r,bloname,prefix):
    # locate blo by header search near its RARC entry: use rarc listing
    hit=[x for x in rarc(bytes(r)) if x[0].endswith(bloname)][0]
    off=bytes(r).find(hit[1]); size=len(hit[1]); assert off>0
    d=bytearray(r[off:off+size]); assert d[:8]==b'SCRNblo2'
    tex,names,mat0,tnt=blo_info(d,0)
    agb=tex.index('AGB_01.bti'); gc=tex.index('controler_01.bti')
    ch=[]
    for i,nm in enumerate(names):
        if nm.startswith('mat_'+prefix):
            e=mat0+0xe8*i; ti=struct.unpack('>H',d[e+0x38:e+0x3a])[0]
            tval=struct.unpack('>H',d[tnt+2*ti:tnt+2*ti+2])[0]
            if tval==agb:
                # find texNo-table slot holding gc
                gslot=[k for k in range(32) if struct.unpack('>H',d[tnt+2*k:tnt+2*k+2])[0]==gc][0]
                d[e+0x38:e+0x3a]=struct.pack('>H',gslot); ch.append(nm)
    print(bloname,'tex',agb,gc,'changed',ch)
    return off,bytes(d)
if __name__=='__main__':
    src,dst=sys.argv[1],sys.argv[2]
    r=bytearray(yaz0(open(src,"rb").read()))
    for bn,pre in [('adv_n_player.blo','P2pli')]:
        try:
            off,nd=patch_blo(r,bn,pre); r[off:off+len(nd)]=nd
        except Exception as ex: print('skip',bn,ex)
    e=yaz0_encode(bytes(r)); assert yaz0(e)==bytes(r)
    open(dst,'wb').write(e); print('wrote',dst,len(e))
