import sys

data = sys.stdin.buffer.read()
pos = 0

def next_int():
    global pos
    n = len(data)
    while pos < n and data[pos] <= 32:
        pos += 1
    num = 0
    while pos < n and data[pos] > 32:
        num = num * 10 + (data[pos] - 48)
        pos += 1
    return num

N = next_int()
Q = next_int()

adj = [[] for _ in range(N)]
for _ in range(N - 1):
    u = next_int()
    v = next_int()
    adj[u].append(v)
    adj[v].append(u)

values = [next_int() for _ in range(N)]

depth_xor = []
stack = [(0, -1, 0)]

while stack:
    u, parent, depth = stack.pop()

    if depth == len(depth_xor):
        depth_xor.append(values[u])
    else:
        depth_xor[depth] ^= values[u]

    next_depth = depth + 1
    for v in adj[u]:
        if v != parent:
            stack.append((v, u, next_depth))

max_depth = len(depth_xor) - 1
B = max_depth.bit_length()
size = 1 << B
ALL = size - 1

dp = [0] * size
for d, val in enumerate(depth_xor):
    dp[d] = val

for i in range(B):
    bit = 1 << i
    for mask in range(size):
        if mask & bit:
            dp[mask] ^= dp[mask ^ bit]

answers = []

for _ in range(Q):
    delta = next_int()

    if delta == 0:
        ans = values[0]
    else:
        k = delta - 1
        forbidden = k & ALL
        ans = dp[ALL ^ forbidden]

    answers.append(str(ans))

sys.stdout.write("\n".join(answers))