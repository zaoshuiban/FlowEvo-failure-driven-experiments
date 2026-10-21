import sys

MOD = 998244353
MAXN = 500000

inv = [0] * (MAXN + 1)
inv[1] = 1
for i in range(2, MAXN + 1):
    inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)

        freq = {}
        for _ in range(n):
            x = next(it)
            freq[x] = freq.get(x, 0) + 1

        ans = 0
        suffix_count = 0

        for value in sorted(freq.keys(), reverse=True):
            count = freq[value]
            suffix_count += count
            ans = (ans + count * inv[suffix_count]) % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()