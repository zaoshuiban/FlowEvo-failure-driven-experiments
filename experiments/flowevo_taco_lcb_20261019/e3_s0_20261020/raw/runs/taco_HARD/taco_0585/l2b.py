import sys

MOD = 998244353

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]

    # Find maximum N to precompute powers of 2.
    idx = 1
    max_n = 0
    for _ in range(t):
        n = data[idx]
        idx += 1
        max_n = max(max_n, n)
        idx += n

    pow2 = [1] * (max_n + 1)
    for i in range(1, max_n + 1):
        pow2[i] = (pow2[i - 1] * 2) % MOD

    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        freq = [0] * (n + 2)
        limit = n + 1

        for _ in range(n):
            a = data[idx]
            idx += 1
            if a <= limit:
                freq[a] += 1

        # Find the smallest positive integer missing from the original sequence.
        mex = 1
        while mex <= limit and freq[mex] > 0:
            mex += 1

        ans = pow2[n]  # contribution of f(S) >= 1 for all subsequences

        product = 1
        prefix_count = 0

        for value in range(1, mex):
            c = freq[value]
            prefix_count += c

            product = product * (pow2[c] - 1) % MOD
            ways = product * pow2[n - prefix_count] % MOD

            ans += ways
            if ans >= MOD:
                ans -= MOD

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()