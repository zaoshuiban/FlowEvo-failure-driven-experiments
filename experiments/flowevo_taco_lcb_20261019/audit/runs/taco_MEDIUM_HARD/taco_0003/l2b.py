import sys

MOD = 1_000_000_007
MAXN = 100000

fact = [1] * (MAXN + 1)
for i in range(1, MAXN + 1):
    fact[i] = fact[i - 1] * i % MOD

invfact = [1] * (MAXN + 1)
invfact[MAXN] = pow(fact[MAXN], MOD - 2, MOD)
for i in range(MAXN, 0, -1):
    invfact[i - 1] = invfact[i] * i % MOD


def comb(n, k):
    if k < 0 or k > n:
        return 0
    return fact[n] * invfact[k] % MOD * invfact[n - k] % MOD


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        max_value = -1
        max_count = 0

        for _ in range(n):
            value = data[idx]
            idx += 1

            if value > max_value:
                max_value = value
                max_count = 1
            elif value == max_value:
                max_count += 1

        total = pow(2, n, MOD)

        if max_count % 2 == 1:
            answers.append(str(total))
        else:
            half = max_count // 2
            bad = comb(max_count, half) * pow(2, n - max_count, MOD) % MOD
            answers.append(str((total - bad) % MOD))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()