#!/usr/bin/env python3
"""One-command build of the Four Swords Adventures two-GameCube-controller mod.

    python3 build.py "<your original USA ISO>" "<output ISO>"

Needs only Python 3 (no extra packages). Your original ISO is only read, never
modified. Re-running after an interruption resumes the disc copy.
"""
import hashlib, os, subprocess, sys, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG_SHA1 = '4bd926835dfbeaae72d01abe5fb581b527154a30'   # G4SE01 rev0 (Redump)
OUT_SHA1 = '336f8607b761ac5d0e0ac76f8cfc9ada683d7855'    # expected result
PATCHES = os.path.join(HERE, 'patches', 'G4SE01_2gc_patches.ini')

def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''): h.update(b)
    return h.hexdigest()

def run(*args):
    print('>', ' '.join(os.path.basename(a) if i < 2 else a for i, a in enumerate(args)))
    subprocess.check_call([sys.executable, *args])

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    orig, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if orig == out: sys.exit('Output must be a different file from the original ISO.')
    print('Checking original ISO...')
    s = sha1(orig)
    if s != ORIG_SHA1:
        print('WARNING: SHA-1 %s does not match the expected USA ISO (%s).' % (s, ORIG_SHA1))
        if '--force' not in sys.argv: sys.exit('Use a clean, unmodified USA (G4SE01) ISO, or pass --force.')
    with tempfile.TemporaryDirectory() as w:
        bd = os.path.join(w, 'disc')
        run(os.path.join(HERE, 'tools', 'gcfs.py'), orig, 'sys', os.path.join(bd, 'sys_orig'))
        run(os.path.join(HERE, 'tools', 'gcfs.py'), orig, 'x', os.path.join(bd, 'files_orig'), '/GC4Sword_usa/entry.arc')
        os.makedirs(os.path.join(bd, 'sys')); os.makedirs(os.path.join(bd, 'files', 'GC4Sword_usa'))
        run(os.path.join(HERE, 'build', 'bake_dol.py'), os.path.join(bd, 'sys_orig', 'main.dol'), PATCHES,
            os.path.join(bd, 'sys', 'main.dol'))
        run(os.path.join(HERE, 'menu', 'patch_menu.py'), os.path.join(bd, 'files_orig', 'GC4Sword_usa', 'entry.arc'),
            os.path.join(bd, 'files', 'GC4Sword_usa', 'entry.arc'))
        print('Copying the used part of the disc (this is the slow step)...')
        run(os.path.join(HERE, 'tools', 'copy_used.py'), orig, out, '1e9')
        run(os.path.join(HERE, 'tools', 'build_iso.py'), orig, bd, out, '/GC4Sword_usa/entry.arc')
    s = sha1(out)
    print('\nOutput: %s\nSHA-1:  %s %s' % (out, s, '(matches the reference build)' if s == OUT_SHA1 else '(differs from the reference build!)'))

if __name__ == '__main__':
    main()
