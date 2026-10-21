import sys

MOD = 10**9 + 7
MAXN = 200000

fact = [1] * (MAXN + 1)
for i in range(2, MAXN + 1):
    fact[i] = fact[i - 1] * i % MOD

data = list(map(int, sys.stdin.buffer.read().split()))
t = data[0]
idx = 1
answers = []

for _ in range(t):
    n = data[idx]
    idx += 1

    a = data[idx:idx + n]
    idx += n

    total_and = a[0]
    for x in a[1:]:
        total_and &= x

    cnt = a.count(total_and)

    if cnt >= 2:
        ans = cnt * (cnt - 1) % MOD
        ans = ans * fact[n - 2] % MOD
    else:
        ans = 0

    answers.append(str(ans))

sys.stdout.write("\n".join(answers))