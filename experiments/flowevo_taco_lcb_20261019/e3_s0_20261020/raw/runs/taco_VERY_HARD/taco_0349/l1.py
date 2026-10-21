import sys

MOD = 998244353


def interpolate_consecutive(y, x):
    # y[i] = P(i), i = 0..d, P has degree <= d.
    d = len(y) - 1
    if x <= d:
        return y[x] % MOD

    xm = x % MOD

    pref = [1] * (d + 2)
    for i in range(d + 1):
        pref[i + 1] = pref[i] * (xm - i) % MOD

    suff = [1] * (d + 2)
    for i in range(d, -1, -1):
        suff[i] = suff[i + 1] * (xm - i) % MOD

    fact = [1] * (d + 1)
    for i in range(1, d + 1):
        fact[i] = fact[i - 1] * i % MOD

    invfact = [1] * (d + 1)
    invfact[d] = pow(fact[d], MOD - 2, MOD)
    for i in range(d, 0, -1):
        invfact[i - 1] = invfact[i] * i % MOD

    result = 0
    for i in range(d + 1):
        numerator = pref[i] * suff[i + 1] % MOD
        term = y[i] * numerator % MOD
        term = term * invfact[i] % MOD
        term = term * invfact[d - i] % MOD

        if (d - i) & 1:
            term = (-term) % MOD

        result = (result + term) % MOD

    return result


def solve():
    n, k = map(int, sys.stdin.buffer.readline().split())

    # H(x) has degree at most n, so prefix sum Q(t) has degree at most n + 1.
    D = n + 1

    comb = [[0] * (n + 2) for _ in range(n + 2)]
    for i in range(n + 2):
        comb[i][0] = comb[i][i] = 1
        for j in range(1, i):
            comb[i][j] = (comb[i - 1][j - 1] + comb[i - 1][j]) % MOD

    H = [0] * (D + 1)

    for x in range(1, D + 1):
        bases = [
            (x - 1) % MOD,          # values < x
            (k - x + 1) % MOD,      # values >= x
            (k - x) % MOD,          # values > x
            x % MOD                 # values <= x
        ]

        powers = []
        for base in bases:
            arr = [1] * (n + 1)
            for e in range(1, n + 1):
                arr[e] = arr[e - 1] * base % MOD
            powers.append(arr)

        pow_less, pow_nonless, pow_greater, pow_nongreater = powers

        total = 0

        for pos in range(1, n + 1):
            left = pos - 1
            right = n - pos

            # suffix[r] = sum of ways with grr >= r
            suffix = [0] * (right + 2)
            for r in range(right, -1, -1):
                ways_right = comb[right][r]
                ways_right = ways_right * pow_greater[r] % MOD
                ways_right = ways_right * pow_nongreater[right - r] % MOD
                suffix[r] = (suffix[r + 1] + ways_right) % MOD

            ways_good = 0

            for l in range(left + 1):
                ways_left = comb[left][l]
                ways_left = ways_left * pow_less[l] % MOD
                ways_left = ways_left * pow_nonless[left - l] % MOD

                if l + 1 <= right:
                    ways_good = (ways_good + ways_left * suffix[l + 1]) % MOD

            total = (total + x * ways_good) % MOD

        H[x] = total

    Q = [0] * (D + 1)
    for t in range(1, D + 1):
        Q[t] = (Q[t - 1] + H[t]) % MOD

    answer = interpolate_consecutive(Q, k)
    print(answer % MOD)


if __name__ == "__main__":
    solve()