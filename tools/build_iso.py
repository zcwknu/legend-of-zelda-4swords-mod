#!/usr/bin/env python3
"""Build the patched GameCube ISO from the untouched original.
Copies the original image, then writes the replacement main.dol and changed
files into the unused area after the last file, and repoints the boot header
(DOL offset) and the FST entries. All other bytes stay identical."""
import sys, os, struct, hashlib, shutil
sys.path.insert(0, os.path.dirname(__file__)); from gcfs import read_fst
def fst_raw(f):
    f.seek(0x424); off, size = struct.unpack('>II', f.read(8)); f.seek(off); return off, bytearray(f.read(size))
def main(orig, builddir, out, changed):
    assert os.path.abspath(orig) != os.path.abspath(out)
    # out must already hold the used region (tools/copy_used.py); pad to full disc size
    with open(out, 'r+b') as g: g.truncate(os.path.getsize(orig))
    with open(out, 'r+b') as f:
        f.seek(0x420); dol_off, fst_off, fst_sz = struct.unpack('>III', f.read(12))
        ents = read_fst(f); _, fst = fst_raw(f)
        n = struct.unpack('>I', fst[8:12])[0]
        used = max([o + s for t, p, o, s in ents if t == 'f'] + [fst_off + fst_sz])
        disc = os.path.getsize(out)
        pos = (used + 0x7fff) & ~0x7fff
        def put(data):
            nonlocal pos
            o = pos; f.seek(o); f.write(data); pos = (pos + len(data) + 0x7fff) & ~0x7fff
            assert pos <= disc, 'out of disc space'; return o
        dol = open(os.path.join(builddir, 'sys', 'main.dol'), 'rb').read()
        o = put(dol); f.seek(0x420); f.write(struct.pack('>I', o)); print('main.dol -> 0x%x (%d bytes)' % (o, len(dol)))
        # map path -> FST index
        idx = {}; i = 1; stack = [(n, '')]
        st = n * 12
        def name(no): e = fst.index(b'\0', st + no); return fst[st + no:e].decode('shift_jis', 'replace')
        while i < n:
            while stack and i >= stack[-1][0]: stack.pop()
            fl = fst[i * 12]; no = int.from_bytes(fst[i * 12 + 1:i * 12 + 4], 'big')
            path = (stack[-1][1] if stack else '') + '/' + name(no)
            if fl: stack.append((struct.unpack('>I', fst[i * 12 + 8:i * 12 + 12])[0], path))
            else: idx[path] = i
            i += 1
        for p in changed:
            data = open(os.path.join(builddir, 'files', p.lstrip('/')), 'rb').read()
            k = idx[p]; o = put(data)
            fst[k * 12 + 4:k * 12 + 12] = struct.pack('>II', o, len(data)); print('%s -> 0x%x (%d bytes)' % (p, o, len(data)))
        f.seek(fst_off); f.write(fst)
    # verify
    with open(out, 'rb') as f:
        f.seek(0x420); dol_off = struct.unpack('>I', f.read(4))[0]; f.seek(dol_off); assert f.read(len(dol)) == dol
        e = {p: (o, s) for t, p, o, s in read_fst(f) if t == 'f'}
        for p in changed:
            o, s = e[p]; f.seek(o); assert f.read(s) == open(os.path.join(builddir, 'files', p.lstrip('/')), 'rb').read()
        f.seek(0); hdr = f.read(6)
    print('verified; game id', hdr, 'size', os.path.getsize(out))
if __name__ == '__main__': main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
