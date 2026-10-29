import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    required = ['total_problems','base_score','correct_coefficient','wrong_coefficient','threshold','max_score','require_unique_correct_count']
    for k in required:
        if k not in parameters:
            raise ValueError('missing parameter: ' + k)
    N = parameters['total_problems']
    B = parameters['base_score']
    A = parameters['correct_coefficient']
    W = parameters['wrong_coefficient']
    T = parameters['threshold']
    M = parameters['max_score']
    req = parameters['require_unique_correct_count']
    for name, val in [('total_problems',N),('base_score',B),('correct_coefficient',A),('wrong_coefficient',W),('threshold',T),('max_score',M)]:
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError(name + ' must be an integer')
    if not isinstance(req, bool):
        raise ValueError('require_unique_correct_count must be a boolean')
    if N < 0 or N > 100000:
        raise ValueError('total_problems out of range')
    if A < 0 or W < 0:
        raise ValueError('coefficients must be nonnegative')
    if A > 10**9 or W > 10**9 or abs(B) > 10**12 or abs(T) > 10**12 or abs(M) > 10**12:
        raise ValueError('parameter magnitude too large')
    if M < T:
        raise ValueError('max_score must be >= threshold')
    if M - T > 10**7:
        raise ValueError('scan range too large')
    intervals = []
    for c in range(N + 1):
        lo = B + A * c - W * (N - c)
        hi = B + A * c
        intervals.append((lo, hi, c))
    def count_at(s):
        cnt = 0
        for lo, hi, c in intervals:
            if lo <= s <= hi:
                cnt += 1
                if cnt > 1 and req:
                    return cnt
        return cnt
    s = T + 1
    while s <= M:
        cnt = count_at(s)
        if req:
            if cnt == 1:
                return str(s)
        else:
            if cnt >= 1:
                return str(s)
        s += 1
    raise ValueError('no qualifying score found in range')

def _selfcheck():
    pass
