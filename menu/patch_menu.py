#!/usr/bin/env python3
"""Patch entry.arc so the Two-Player rows of the player-count menus show
GameCube controllers instead of Game Boy Advances.

  * adv_n_player.blo  (Hyrulean Adventure): already lists controler_01.bti,
    so the four P2 icon materials are simply pointed at it.
  * bat_n_player.blo  (Shadow Battle): has no controller texture, so
    controler_01.bti (already in entry.arc/timg) is added to the layout's
    texture list, the P2 icon materials are pointed at it, and the archive
    is repacked around the slightly larger layout file.

Usage: patch_menu.py <original entry.arc> <output entry.arc>
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rarc import yaz0
from yaz0enc import yaz0_encode

AGB, GC = 'AGB_01.bti', 'controler_01.bti'

# ---------------------------------------------------------------- BLO (J2D screen, "SCRNblo2")
def chunks(d):
    o, ch = 0x20, {}
    while o < len(d):
        t = bytes(d[o:o + 4]); sz = struct.unpack('>I', d[o + 4:o + 8])[0]
        ch.setdefault(t, (o, sz))
        if t == b'EXT1' or sz == 0: break
        o += sz
    return ch

def textures(d):
    o, _ = chunks(d)[b'TEX1']; tb = o + 0x10
    n = struct.unpack('>H', d[tb:tb + 2])[0]; out = []
    for i in range(n):
        q = struct.unpack('>H', d[tb + 2 + 2 * i:tb + 4 + 2 * i])[0]
        out.append(bytes(d[tb + q + 2:tb + q + 2 + d[tb + q + 1]]).decode())
    return out

def materials(d):
    m, _ = chunks(d)[b'MAT1']
    n = struct.unpack('>H', d[m + 8:m + 10])[0]
    offs = struct.unpack('>20I', d[m + 0xc:m + 0x5c])
    nt = m + offs[2]; names = []
    for i in range(n):
        _, q = struct.unpack('>HH', d[nt + 4 + 4 * i:nt + 8 + 4 * i])
        names.append(bytes(d[nt + q:d.index(b'\0', nt + q)]).decode())
    nxt = min(x for x in offs[12:] if x > offs[11])
    return names, m + offs[0], m + offs[11], (nxt - offs[11]) // 2   # names, mat data, texNo table, table slots

def add_texture(d, name):
    """Append a texture reference to TEX1; returns (new blo, new texture index)."""
    o, sz = chunks(d)[b'TEX1']
    names = textures(d) + [name]
    tab = struct.pack('>H', len(names)); strs = b''
    base = 2 + 2 * len(names)
    for nm in names:
        tab += struct.pack('>H', base + len(strs)); strs += bytes([2, len(nm)]) + nm.encode()
    body = struct.pack('>HHI', len(names), 0xffff, 0x10) + tab + strs
    total = (8 + len(body) + 31) & ~31
    chunk = b'TEX1' + struct.pack('>I', total) + body + bytes(total - 8 - len(body))
    nd = bytearray(d[:o]) + chunk + d[o + sz:]
    nd[8:12] = struct.pack('>I', len(nd))
    return nd, len(names) - 1

def point_icons(d, prefix, tex_from, tex_to):
    """Point every material named mat_<prefix>* that uses tex_from at tex_to."""
    names, mat0, tnt, slots = materials(d)
    tv = lambda s: struct.unpack('>H', d[tnt + 2 * s:tnt + 2 * s + 2])[0]
    used = set()
    for i in range(len(names)):
        for k in range(8):
            s = struct.unpack('>H', d[mat0 + 0xe8 * i + 0x34 + 2 * k:mat0 + 0xe8 * i + 0x36 + 2 * k])[0]
            if s != 0xffff: used.add(s)
    slot = next((s for s in sorted(used) if tv(s) == tex_to), None)
    if slot is None:                                 # use the first free (padding) slot of the texNo table
        slot = max(used) + 1; assert slot < slots, 'no free texNo slot'
        d[tnt + 2 * slot:tnt + 2 * slot + 2] = struct.pack('>H', tex_to)
    changed = []
    for i, nm in enumerate(names):
        e = mat0 + 0xe8 * i + 0x38
        if nm.startswith('mat_' + prefix) and tv(struct.unpack('>H', d[e:e + 2])[0]) == tex_from:
            d[e:e + 2] = struct.pack('>H', slot); changed.append(nm)
    return changed

# ---------------------------------------------------------------- RARC
def rarc_files(r):
    ih = 0x20; dat = struct.unpack('>I', r[0xc:0x10])[0] + ih
    nn, noff, ne, eoff, strsz, stroff = struct.unpack('>6I', r[ih:ih + 24])
    out = {}
    for k in range(ne):
        e = ih + eoff + 20 * k
        fl, no, doff, sz = struct.unpack('>HHII', r[e + 4:e + 16])
        if fl & 0x200: continue
        nm = bytes(r[ih + stroff + no:r.index(b'\0', ih + stroff + no)]).decode()
        out[nm] = (e, dat + doff, sz)
    return out, dat

def rarc_replace(r, name, new):
    files, dat = rarc_files(r)
    e, off, sz = files[name]
    old_al, new_al = (sz + 31) & ~31, (len(new) + 31) & ~31
    delta = new_al - old_al
    r = bytearray(r[:off]) + new + bytes(new_al - len(new)) + r[off + old_al:]
    r[e + 12:e + 16] = struct.pack('>I', len(new))
    if delta:
        for nm, (e2, off2, _) in files.items():
            if off2 > off: r[e2 + 8:e2 + 12] = struct.pack('>I', off2 + delta - dat)
        for f in (0x4, 0x10, 0x14):                  # file size, data length, MRAM size
            v = struct.unpack('>I', r[f:f + 4])[0]
            if f == 0x4 or v: r[f:f + 4] = struct.pack('>I', v + delta)
    return r

def main(src, dst):
    r = bytearray(yaz0(open(src, 'rb').read()))
    files, _ = rarc_files(r)
    assert 'controler_01.bti' in files, 'controller texture missing from archive'
    for blo in ('adv_n_player.blo', 'bat_n_player.blo'):
        _, off, sz = rarc_files(r)[0][blo]
        d = bytearray(r[off:off + sz]); assert d[:8] == b'SCRNblo2'
        tex = textures(d)
        if GC not in tex:
            d, gi = add_texture(d, GC); added = ' (texture added)'
        else:
            gi, added = tex.index(GC), ''
        ch = point_icons(d, 'P2pli', tex.index(AGB), gi)
        assert len(ch) == 4, ch
        print('%s: %d Two-Player icons -> %s%s' % (blo, len(ch), GC, added))
        r = rarc_replace(r, blo, bytes(d))
    e = yaz0_encode(bytes(r)); assert yaz0(e) == bytes(r)
    open(dst, 'wb').write(e); print('wrote', dst, len(e))

if __name__ == '__main__':
    main(*sys.argv[1:3])
