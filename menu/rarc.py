#!/usr/bin/env python3
"""Yaz0 + RARC list/extract."""
import sys,struct,os
def yaz0(d):
    if d[:4]!=b'Yaz0': return d
    n=struct.unpack('>I',d[4:8])[0]; o=bytearray(); i=16
    while len(o)<n:
        c=d[i]; i+=1
        for b in range(8):
            if len(o)>=n: break
            if c&(0x80>>b): o.append(d[i]); i+=1
            else:
                b1,b2=d[i],d[i+1]; i+=2; dist=((b1&0xf)<<8|b2)+1; ln=b1>>4
                if ln==0: ln=d[i]+0x12; i+=1
                else: ln+=2
                for _ in range(ln): o.append(o[-dist])
    return bytes(o)
def rarc(d):
    dataoff=struct.unpack('>I',d[0xc:0x10])[0]+0x20
    ih=0x20; nn,noff,ne,eoff,strsz,stroff=struct.unpack('>IIIIII',d[ih:ih+24])
    noff+=ih; eoff+=ih; stroff+=ih
    def s(o): e=d.index(b'\0',stroff+o); return d[stroff+o:e].decode('shift_jis','replace')
    out=[]
    def walk(ni,path):
        typ,nameo,h,cnt,first=struct.unpack('>4sIHHI',d[noff+ni*16:noff+ni*16+16])
        for k in range(cnt):
            e=eoff+(first+k)*20
            idx,hh,fl,no,doff,sz=struct.unpack('>HHHHII',d[e:e+16]); nm=s(no)
            if nm in('.','..'): continue
            if fl&0x200 or (fl>>8)&2: walk(doff,path+'/'+nm)
            else: out.append((path+'/'+nm,d[dataoff+doff:dataoff+doff+sz]))
    walk(0,'')
    return out
if __name__=='__main__':
    d=yaz0(open(sys.argv[1],'rb').read())
    for p,b in rarc(d):
        print('%8d %s'%(len(b),p))
        if len(sys.argv)>2:
            dst=os.path.join(sys.argv[2],p.lstrip('/')); os.makedirs(os.path.dirname(dst),exist_ok=True); open(dst,'wb').write(b)
