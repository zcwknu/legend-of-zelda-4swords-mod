#!/usr/bin/env python3
"""Bake the Dolphin [OnFrame] patch set into main.dol.
The code cave (Dolphin build: 0x80001800-0x80003000) is relocated into a new DOL text
section placed after the game's debug stack (0x80555F80), and OSInit's
ArenaLo constants are raised so the heap starts after the cave."""
import re, struct, sys
OLD = 0x80001800; NB = 0x80555F80; CSIZE = 0x1800; NEND = NB + CSIZE
LO = OLD & 0xffff
def relo(a): return a - OLD + NB
# cave words that are data (floats/flags/tags), copied verbatim: exp5 flag + scale constants, exp6 panel anchors,
# exp11/exp12 per-port timers and trigger flags (0x80001A00-0x80001A60) are
# zero-filled and never written by the patch file
DATA = [(0x80002A40, 0x80002A50), (0x80002BE0, 0x80002BF0)]
def isdata(a): return any(s <= a < e for s, e in DATA)
def incave(a): return OLD <= a < OLD + CSIZE

def load_patches(ini):
    t = open(ini).read()
    on = t.split('[OnFrame_Enabled]')[1]
    enabled = set(l.strip() for l in on.splitlines() if l.startswith('$'))
    body = t.split('[OnFrame]')[1].split('[OnFrame_Enabled]')[0]
    P = []; cur = None
    for l in body.splitlines():
        l = l.strip()
        if l.startswith('$'): cur = l
        m = re.match(r'0x([0-9A-Fa-f]+):dword:0x([0-9A-Fa-f]+)', l)
        if m and cur in enabled: P.append((int(m[1], 16), int(m[2], 16)))
    return P

def fix_branch(pc, w, newpc):
    if w >> 26 == 18 and not (w & 2):
        off = w & 0x3fffffc
        if off & 0x2000000: off -= 0x4000000
        tgt = pc + off
        ntgt = relo(tgt) if incave(tgt) else tgt
        d = ntgt - newpc; assert -0x2000000 <= d < 0x2000000
        return (w & 0xfc000003) | (d & 0x3fffffc)
    if w >> 26 == 16 and not (w & 2):
        off = w & 0xfffc
        if off & 0x8000: off -= 0x10000
        assert incave(pc + off) == incave(pc), 'bc crosses cave boundary at %08x' % pc
    return w

def main(src, ini, dst):
    d = bytearray(open(src, 'rb').read())
    offs = list(struct.unpack('>18I', d[0:72])); addr = list(struct.unpack('>18I', d[72:144])); sz = list(struct.unpack('>18I', d[144:216]))
    def a2o(a):
        for i in range(18):
            if sz[i] and addr[i] <= a < addr[i] + sz[i]: return offs[i] + a - addr[i]
        raise ValueError('%08x not in DOL' % a)
    P = load_patches(ini)
    cave = bytearray(CSIZE); n_dol = 0
    for a, v in P:
        if incave(a):
            cave[a - OLD:a - OLD + 4] = struct.pack('>I', v if isdata(a) else fix_branch(a, v, relo(a)))
        else:
            o = a2o(a); d[o:o + 4] = struct.pack('>I', fix_branch(a, v, a)); n_dol += 1
    # absolute refs to cave data: lis rX,0x8000 ; D-form with base rX and imm in cave range
    W = lambda i: struct.unpack('>I', cave[i:i + 4])[0]
    nfix = 0
    for i in range(0, CSIZE, 4):
        w = W(i)
        if w >> 26 == 15 and (w & 0xffff) == 0x8000 and ((w >> 16) & 31) == 0:
            rx = (w >> 21) & 31
            for j in range(i + 4, min(i + 0x40, CSIZE), 4):
                w2 = W(j); op = w2 >> 26
                if op in (14, 15, 32, 34, 40) and ((w2 >> 21) & 31) == rx and ((w2 >> 16) & 31) != rx: break
                if op in (14, 32, 34, 36, 38, 40, 44, 48, 52) and ((w2 >> 16) & 31) == rx:
                    imm = w2 & 0xffff
                    if LO <= imm < LO + CSIZE:
                        na = relo(0x80000000 + imm); assert (na & 0xffff) < 0x8000
                        cave[j:j + 4] = struct.pack('>I', (w2 & 0xffff0000) | (na & 0xffff)); nfix += 1
                        cave[i:i + 4] = struct.pack('>I', (w & 0xffff0000) | (na >> 16))
                        if op == 14: break
    # sanity: every lis 0x8000 must have been relocated, and no cave word may still point into the Dolphin cave
    for i in range(0, CSIZE, 4):
        w = W(i)
        if w >> 26 in (14, 32, 34, 36, 38, 40, 44, 48, 52) and LO <= (w & 0xffff) < LO + CSIZE and ((w >> 16) & 31) != 0:
            prev = [W(j) for j in range(max(0, i - 0x40), i, 4)]
            assert not any(p >> 26 == 15 and (p & 0xffff) == 0x8000 for p in prev), 'unrelocated data ref at +0x%x' % i
    # sanity: no remaining 0x8000 lis
    for i in range(0, CSIZE, 4):
        w = W(i); assert not (w >> 26 == 15 and (w & 0xffff) == 0x8000), hex(i)
    # OSInit ArenaLo constants
    for lis_a, val_old in ((0x8003FBD4, 0x80555F80), (0x8003FC0C, 0x80553F70)):
        o = a2o(lis_a); w1, w2 = struct.unpack('>II', d[o:o + 8])
        cur = ((w1 & 0xffff) << 16) + struct.unpack('>h', struct.pack('>H', w2 & 0xffff))[0]
        assert cur & 0xffffffff == val_old, (hex(lis_a), hex(cur))
        ha = (NEND + 0x8000) >> 16; lo = NEND & 0xffff
        d[o:o + 8] = struct.pack('>II', (w1 & 0xffff0000) | ha, (w2 & 0xffff0000) | lo)
    # add text section 2
    assert sz[2] == 0
    end = max(offs[i] + sz[i] for i in range(18) if sz[i]); end = (end + 31) & ~31
    d = d[:end] + bytes(end - len(d)) if len(d) < end else d[:end]
    offs[2], addr[2], sz[2] = end, NB, CSIZE
    d += cave
    d[0:72] = struct.pack('>18I', *offs); d[72:144] = struct.pack('>18I', *addr); d[144:216] = struct.pack('>18I', *sz)
    open(dst, 'wb').write(d)
    print('patches: %d total, %d in DOL, %d cave words; %d data refs relocated' % (len(P), n_dol, sum(1 for a, _ in P if incave(a)), nfix))
    print('cave %08x-%08x at file 0x%x; ArenaLo -> %08x; dol size %d' % (NB, NEND, end, NEND, len(d)))
if __name__ == '__main__': main(*sys.argv[1:4])
