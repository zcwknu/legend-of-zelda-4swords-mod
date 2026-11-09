#!/usr/bin/env python3
"""GameCube disc FST lister/extractor (read-only on the ISO)."""
import sys,struct,os
def read_fst(f):
    f.seek(0x424); fst_off,fst_sz=struct.unpack('>II',f.read(8))
    f.seek(fst_off); d=f.read(fst_sz)
    n=struct.unpack('>I',d[8:12])[0]; st=n*12
    def name(o): e=d.index(b'\0',st+o); return d[st+o:e].decode('shift_jis','replace')
    ents=[]; stack=[(n,'')]
    i=1
    while i<n:
        while stack and i>=stack[-1][0]: stack.pop()
        fl,no,a,b=d[i*12],int.from_bytes(d[i*12+1:i*12+4],'big'),*struct.unpack('>II',d[i*12+4:i*12+12])
        path=(stack[-1][1] if stack else '')+'/'+name(no)
        if fl: ents.append(('d',path,0,0)); stack.append((b,path))
        else: ents.append(('f',path,a,b))
        i+=1
    return ents
if __name__=='__main__':
    iso=sys.argv[1]; f=open(iso,'rb'); ents=read_fst(f)
    if sys.argv[2]=='ls':
        for t,p,o,s in ents: print(t,'%08x'%o,'%9d'%s,p)
    elif sys.argv[2]=='x':
        out=sys.argv[3]
        for pat in sys.argv[4:]:
            for t,p,o,s in ents:
                if t=='f' and (p==pat or p.startswith(pat)):
                    dst=os.path.join(out,p.lstrip('/')); os.makedirs(os.path.dirname(dst),exist_ok=True)
                    f.seek(o); open(dst,'wb').write(f.read(s)); print('x',p,s)
    elif sys.argv[2]=='sys':
        out=sys.argv[3]; os.makedirs(out,exist_ok=True)
        f.seek(0); open(out+'/boot.bin','wb').write(f.read(0x440)); open(out+'/bi2.bin','wb').write(f.read(0x2000))
        f.seek(0x2440); hdr=f.read(0x20); sz=struct.unpack('>I',hdr[0x14:0x18])[0]+struct.unpack('>I',hdr[0x18:0x1c])[0]
        f.seek(0x2440); open(out+'/apploader.img','wb').write(f.read(0x20+sz))
        f.seek(0x420); dol=struct.unpack('>I',f.read(4))[0]; f.seek(dol); h=f.read(0x100)
        offs=struct.unpack('>18I',h[0:72]); sizes=struct.unpack('>18I',h[0x90:0x90+72])
        end=max(o+s for o,s in zip(offs,sizes) if s); f.seek(dol); open(out+'/main.dol','wb').write(f.read(end))
        print('dol size',end)
