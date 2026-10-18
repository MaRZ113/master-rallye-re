"""T2 reconnaissance: try the PC tag100 grammar on a PS2 .BSP payload.

Read-only. The PS2 file has no leading tag word; the first five u32 are assumed to be the same
header counts as PC tag100. Reports how far a parameterised walk of the PC grammar gets.
"""
import struct
import sys
from pathlib import Path


def walk(data, start, leading_words, extra_non_root=0, limit=5_000_000):
    """Iterative walk of the PC grammar with `leading_words` u32 fields per node. Returns stats."""
    o = start
    n = planes = lists = 0
    role = {'child': 0, 'sibling': 0, 'alloc36': 0}
    stack = []  # nodes waiting for a sibling flag
    pending = True
    try:
        def b():
            nonlocal o
            v = data[o]
            o += 1
            if v not in (0, 1):
                raise ValueError(f'non-boolean {v} at {o - 1:#x}')
            return v
        while pending or stack:
            if not pending:
                stack.pop()
                if not b():
                    continue
                role['sibling' if b() else 'alloc36'] += 1
            pending = False
            o += 4 * leading_words + (extra_non_root if n else 0)
            if b():
                o += 20
                planes += 1
            if b():
                (cnt,) = struct.unpack_from('<I', data, o)
                o += 4 + 20 * cnt
                lists += 1
            n += 1
            if n > limit:
                raise ValueError('limit')
            if b():
                role['child' if b() else 'alloc36'] += 1
                stack.append(n)
                pending = True
            else:
                if b():
                    role['sibling' if b() else 'alloc36'] += 1
                    pending = True
    except (ValueError, IndexError, struct.error) as exc:
        return {'error': str(exc), 'nodes': n, 'planes': planes, 'offset': o}
    return {'nodes': n, 'planes': planes, 'lists': lists, 'roles': role, 'end_offset': o, 'size': len(data)}


def main(path):
    data = Path(path).read_bytes()
    header = struct.unpack_from('<5I', data, 0)
    print('header words', header)
    for start in (20, 24):
        for extra in (0, 1):
            print('start', start, 'extra byte on non-root nodes', extra, walk(data, start, 2, extra))


if __name__ == '__main__':
    main(sys.argv[1])
