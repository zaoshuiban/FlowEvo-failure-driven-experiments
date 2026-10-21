import sys

MOD = 998244353

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    N = int(data[0])
    K = int(data[1])
    S = data[2].decode()

    L = K - 1
    M = 1 << L
    mask_all = M - 1

    # bad[w] is True iff the K-bit number w represents a palindrome.
    bad = [False] * (1 << K)
    for w in range(1 << K):
        rev = 0
        x = w
        for _ in range(K):
            rev = (rev << 1) | (x & 1)
            x >>= 1
        bad[w] = (rev == w)

    dp = [0] * M
    dp[0] = 1

    for i, ch in enumerate(S):
        if ch == 'A':
            bits = (0,)
        elif ch == 'B':
            bits = (1,)
        else:
            bits = (0, 1)

        ndp = [0] * M
        check = (i >= K - 1)

        for mask, val in enumerate(dp):
            if val == 0:
                continue

            for b in bits:
                window = (mask << 1) | b

                if check and bad[window]:
                    continue

                new_mask = window & mask_all
                ndp[new_mask] += val
                if ndp[new_mask] >= MOD:
                    ndp[new_mask] -= MOD

        dp = ndp

    print(sum(dp) % MOD)


if __name__ == "__main__":
    solve()