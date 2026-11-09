#!/usr/bin/env python3
"""Resumable copy of the used region of a GC disc image (header..last file), time-boxed."""
import sys, os, time, struct
sys.path.insert(0, os.path.dirname(__file__)); from gcfs import read_fst
src, dst, budget = sys.argv[1], sys.argv[2], float(sys.argv[3])
f = open(src, 'rb'); f.seek(0x424); fo, fs = struct.unpack('>II', f.read(8))
used = max([o + s for t, p, o, s in read_fst(f) if t == 'f'] + [fo + fs])
cur = os.path.getsize(dst) if os.path.exists(dst) else 0
cur = min(cur, used) & ~0xfffff  # back off to a 1 MiB boundary
t0 = time.time()
with open(dst, 'r+b' if os.path.exists(dst) else 'wb') as g:
    g.truncate(cur); f.seek(cur); g.seek(cur)
    while cur < used and time.time() - t0 < budget:
        b = f.read(min(8 << 20, used - cur)); g.write(b); cur += len(b)
print('copied %d / %d (%.1f%%)' % (cur, used, 100 * cur / used), 'DONE' if cur >= used else 'MORE')
