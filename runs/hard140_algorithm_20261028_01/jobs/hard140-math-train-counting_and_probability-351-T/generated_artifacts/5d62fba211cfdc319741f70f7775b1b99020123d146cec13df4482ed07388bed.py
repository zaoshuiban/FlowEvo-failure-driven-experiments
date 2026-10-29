import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    required = ['target_x', 'target_y', 'max_steps']
    for key in required:
        if key not in parameters:
            raise ValueError('missing parameter: ' + key)
    tx = parameters['target_x']
    ty = parameters['target_y']
    N = parameters['max_steps']
    for v in (tx, ty, N):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError('parameters must be integers')
    if N < 0:
        raise ValueError('max_steps must be nonnegative')
    if N > 40:
        raise ValueError('max_steps too large for exact computation')
    if abs(tx) > N or abs(ty) > N:
        return '0'
    # Parity: reachable only if tx+ty even and |tx|+|ty| <= N
    if (tx + ty) % 2 != 0:
        return '0'
    if abs(tx) + abs(ty) > N:
        return '0'
    # DP over states (x,y) reachable within N steps, tracking probability mass
    # of walks that have NOT yet hit target. We compute probability of hitting by N.
    # Use exact integer counts over 4^N prefixes.
    # State: dict (x,y) -> count of walks of current length that have not hit target yet.
    # Start at (0,0). If target is (0,0), hit at step 0.
    if tx == 0 and ty == 0:
        return '1'
    # counts of non-hit walks at each step
    cur = {(0, 0): 1}
    hit_count = 0
    for step in range(1, N + 1):
        nxt = {}
        for (x, y), c in cur.items():
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = x + dx
                ny = y + dy
                if nx == tx and ny == ty:
                    hit_count += c
                else:
                    key = (nx, ny)
                    nxt[key] = nxt.get(key, 0) + c
        cur = nxt
    total = 4 ** N
    # hit_count is number of length-N prefixes whose first hit is at some step <= N
    # (each non-hit prefix of length step-1 that steps onto target contributes c prefixes of length N)
    # Wait: hit_count accumulates c for each non-hit prefix of length step-1 that steps onto target.
    # Each such prefix extends to 4^(N-step) full length-N prefixes. So we must weight.
    # Recompute properly with weighting.
    cur = {(0, 0): 1}
    hit_weighted = 0
    for step in range(1, N + 1):
        nxt = {}
        remaining = N - step
        for (x, y), c in cur.items():
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = x + dx
                ny = y + dy
                if nx == tx and ny == ty:
                    hit_weighted += c * (4 ** remaining)
                else:
                    key = (nx, ny)
                    nxt[key] = nxt.get(key, 0) + c
        cur = nxt
    g = math.gcd(hit_weighted, total)
    m = hit_weighted // g
    n = total // g
    return str(m + n)

def _self_test():
    assert solve({'target_x': 2, 'target_y': 2, 'max_steps': 6}) == '2099'
    assert solve({'target_x': 0, 'target_y': 0, 'max_steps': 0}) == '1'
    assert solve({'target_x': 1, 'target_y': 0, 'max_steps': 1}) == '5'
    assert solve({'target_x': 1, 'target_y': 1, 'max_steps': 1}) == '0'

_self_test()
