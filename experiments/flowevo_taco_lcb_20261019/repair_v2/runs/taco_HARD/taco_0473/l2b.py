import sys

MOD = 1_000_000_007

data = list(map(int, sys.stdin.buffer.read().split()))
if not data:
    sys.exit()

t = data[0]
tests = []
max_nk = 1
idx = 1

for _ in range(t):
    n = data[idx]
    k = data[idx + 1]
    m = data[idx + 2]
    idx += 3
    tests.append((n, k, m))
    if n + k > max_nk:
        max_nk = n + k

inv = [0] * (max_nk + 1)
inv[1] = 1

for i in range(2, max_nk + 1):
    inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD

ans = []

for n, k, m in tests:
    q0 = (n - 1) * inv[n] % MOD

    if m & 1:
        fail = pow(q0, (m + 1) // 2, MOD)
    else:
        q1 = (n + k - 1) * inv[n + k] % MOD
        fail = pow(q0, m // 2, MOD) * q1 % MOD

    ans.append(str((1 - fail) % MOD))

sys.stdout.write("\n".join(ans))