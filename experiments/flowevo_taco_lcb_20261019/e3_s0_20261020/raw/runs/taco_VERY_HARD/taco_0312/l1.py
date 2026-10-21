import sys
from bisect import bisect_left

MOD = 998244353

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    m = next(it)

    d = [next(it) for _ in range(n)]
    queries = [(next(it), next(it)) for _ in range(m)]

    d.sort()
    pref = [0] * (n + 1)
    for i, x in enumerate(d):
        pref[i + 1] = pref[i] + x

    total = pref[n]

    inv = [0] * (n + 2)
    inv[1] = 1
    for i in range(2, n + 2):
        inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD

    answers = []

    for a, b in queries:
        idx = bisect_left(d, b)
        k = n - idx

        if a > k:
            answers.append("0")
            continue

        sum_ge = total - pref[idx]
        sum_lt = total - sum_ge

        part1 = (sum_ge % MOD) * ((k - a) % MOD) % MOD * inv[k] % MOD
        part2 = (sum_lt % MOD) * ((k + 1 - a) % MOD) % MOD * inv[k + 1] % MOD

        answers.append(str((part1 + part2) % MOD))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()