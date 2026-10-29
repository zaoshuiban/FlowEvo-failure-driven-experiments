import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    required = ['n', 'base', 'correct_weight', 'wrong_weight', 'threshold']
    for key in required:
        if key not in parameters:
            raise ValueError('missing parameter: ' + key)
    vals = {}
    for key in required:
        v = parameters[key]
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError('parameter must be integer: ' + key)
        vals[key] = v
    n = vals['n']
    base = vals['base']
    a = vals['correct_weight']
    b = vals['wrong_weight']
    T = vals['threshold']
    if n < 0 or n > 100000:
        raise ValueError('n out of range')
    if a < 0 or b < 0:
        raise ValueError('weights must be nonnegative')
    if a > 1000000 or b > 1000000:
        raise ValueError('weights too large')
    if abs(base) > 1000000000 or abs(T) > 1000000000:
        raise ValueError('base or threshold out of range')
    # For each c in [0,n], achievable scores form integer interval
    # lo(c) = base + a*c - b*(n-c), hi(c) = base + a*c.
    # A score s is determining iff exactly one c has lo(c) <= s <= hi(c).
    # We search s = T+1, T+2, ... for the first determining score.
    # Bound the search: the maximum possible score is base + a*n.
    max_score = base + a * n
    if max_score <= T:
        raise ValueError('no score above threshold is achievable')
    # Precompute intervals
    intervals = []
    for c in range(n + 1):
        hi = base + a * c
        lo = hi - b * (n - c)
        intervals.append((lo, hi))
    # Search upward from T+1. The number of candidate scores is bounded by
    # max_score - T, which could be large if weights are huge. But we can
    # reason: as s increases, the set of feasible c changes only at interval
    # endpoints. We can iterate over candidate s values efficiently by
    # considering the union of intervals and finding the smallest s > T
    # covered by exactly one interval.
    # Collect all interval endpoints (lo and hi+1) as breakpoints.
    points = set()
    points.add(T + 1)
    for lo, hi in intervals:
        if hi >= T + 1:
            points.add(lo)
            points.add(hi + 1)
    points = sorted(p for p in points if p > T)
    # For each segment between consecutive breakpoints, the set of covering
    # intervals is constant. Check the start of each segment.
    for idx in range(len(points)):
        s = points[idx]
        if s > max_score:
            break
        count = 0
        for lo, hi in intervals:
            if lo <= s <= hi:
                count += 1
                if count > 1:
                    break
        if count == 1:
            return str(s)
    raise ValueError('no determining score found above threshold')

def _unused():
    pass
