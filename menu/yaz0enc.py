import struct
def yaz0_encode(src):
    """Simple greedy Yaz0 encoder with hash-chain search (window 4096, max len 273)."""
    n=len(src); out=bytearray(b'Yaz0'+struct.pack('>I',n)+b'\0'*8)
    pos=0; head={}
    def insert(p):
        if p+3<=n: head.setdefault(src[p:p+3],[]).append(p)
    def find(p):
        if p+3>n: return 0,0
        best=0;bd=0
        lst=head.get(src[p:p+3])
        if not lst: return 0,0
        mx=min(273,n-p)
        for q in reversed(lst):
            if p-q>4096: break
            l=3
            while l<mx and src[q+l]==src[p+l]: l+=1
            if l>best: best=l;bd=p-q
            if l==mx: break
        return best,bd
    while pos<n:
        ci=len(out); out.append(0); code=0
        for b in range(8):
            if pos>=n: break
            l,dd=find(pos)
            if l>=3:
                dd-=1
                if l>=0x12: out+=bytes([dd>>8,dd&0xff,l-0x12])
                else: out+=bytes([((l-2)<<4)|(dd>>8),dd&0xff])
                for k in range(l): insert(pos+k)
                pos+=l
            else:
                code|=0x80>>b; out.append(src[pos]); insert(pos); pos+=1
        out[ci]=code
    return bytes(out)
