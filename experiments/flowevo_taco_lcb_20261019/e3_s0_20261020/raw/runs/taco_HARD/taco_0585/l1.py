import sys

MOD = 998244353
MAXN = 500005

pow2 = [1] * MAXN
for i in range(1, MAXN):
    pow2[i] = (pow2[i - 1] * 2) % MOD


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        cnt = [0] * (n + 2)

        for _ in range(n):
            a = data[idx]
            idx += 1
            if a <= n:
                cnt[a] += 1

        ans = pow2[n]  # contribution of f(S) >= 1, i.e. all subsequences

        prefix_count = 0
        product = 1

        for m in range(1, n + 1):
            c = cnt[m]
            if c == 0:
                break

            prefix_count += c
            product = product * (pow2[c] - 1) % MOD

            # Number of subsequences containing every value from 1 to m
            cur = product * pow2[n - prefix_count] % MOD
            ans = (ans + cur) % MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()