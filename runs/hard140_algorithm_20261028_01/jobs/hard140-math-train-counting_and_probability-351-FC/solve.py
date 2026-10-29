import math
from fractions import Fraction

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    required = ['target_x', 'target_y', 'max_steps', 'step_set']
    for key in required:
        if key not in parameters:
            raise ValueError('missing parameter: ' + key)
    tx = parameters['target_x']
    ty = parameters['target_y']
    N = parameters['max_steps']
    steps = parameters['step_set']
    if isinstance(tx, bool) or isinstance(ty, bool) or isinstance(N, bool):
        raise ValueError('booleans are not integers')
    if not isinstance(tx, int) or not isinstance(ty, int) or not isinstance(N, int):
        raise ValueError('target coordinates and max_steps must be integers')
    if N < 0:
        raise ValueError('max_steps must be nonnegative')
    if N > 200:
        raise ValueError('max_steps too large')
    if not isinstance(steps, list) or len(steps) == 0:
        raise ValueError('step_set must be a nonempty list')
    if len(steps) > 16:
        raise ValueError('too many steps')
    parsed = []
    for s in steps:
        if not isinstance(s, list) or len(s) != 2:
            raise ValueError('each step must be a pair')
        dx = s[0]
        dy = s[1]
        if isinstance(dx, bool) or isinstance(dy, bool):
            raise ValueError('booleans are not integers')
        if not isinstance(dx, int) or not isinstance(dy, int):
            raise ValueError('step components must be integers')
        if abs(dx) > 100 or abs(dy) > 100:
            raise ValueError('step component too large')
        parsed.append((dx, dy))
    if abs(tx) > 1000 or abs(ty) > 1000:
        raise ValueError('target too far')
    k = len(parsed)
    # absorbing DP: states are positions not yet equal to target
    # counts as integers
    current = {(0, 0): 1}
    hit_counts = []
    for t in range(1, N + 1):
        nxt = {}
        hits = 0
        for (x, y), c in current.items():
            for (dx, dy) in parsed:
                nx = x + dx
                ny = y + dy
                if nx == tx and ny == ty:
                    hits += c
                else:
                    key = (nx, ny)
                    nxt[key] = nxt.get(key, 0) + c
        hit_counts.append(hits)
        current = nxt
        if not current:
            # no non-target states remain; further hits are zero
            for _ in range(t, N):
                hit_counts.append(0)
            break
    # probability = sum_t hits_t / k^t
    total = Fraction(0, 1)
    for idx in range(len(hit_counts)):
        t = idx + 1
        total += Fraction(hit_counts[idx], k ** t)
    m = total.numerator
    n = total.denominator
    return str(m + n)
