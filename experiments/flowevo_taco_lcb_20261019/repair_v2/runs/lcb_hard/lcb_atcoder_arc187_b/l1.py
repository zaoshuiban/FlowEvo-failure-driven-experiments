import sys
from array import array

MOD = 998244353


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, M = data[0], data[1]
    B = data[2:2 + N]

    # Prefix information
    pre_unk = [0] * N
    pre_min = [0] * N

    unknown = 0
    minimum_fixed = M + 1

    for i, x in enumerate(B):
        if x == -1:
            unknown += 1
        else:
            if x < minimum_fixed:
                minimum_fixed = x
        pre_unk[i] = unknown
        pre_min[i] = minimum_fixed

    # Suffix information
    suf_unk = [0] * N
    suf_max = [0] * N

    unknown = 0
    maximum_fixed = 0

    for i in range(N - 1, -1, -1):
        x = B[i]
        if x == -1:
            unknown += 1
        else:
            if x > maximum_fixed:
                maximum_fixed = x
        suf_unk[i] = unknown
        suf_max[i] = maximum_fixed

    q = pre_unk[-1]

    # pow_table[base][exp] = base^exp mod MOD
    pow_table = []
    for base in range(M + 1):
        row = array('I', [1]) * (N + 1)
        value = 1
        for exp in range(1, N + 1):
            value = value * base % MOD
            row[exp] = value
        pow_table.append(row)

    # Every assignment contributes at least 1 connected component.
    ans = pow(M, q, MOD)

    # Add the contribution of every possible separating cut.
    for k in range(1, N):
        uL = pre_unk[k - 1]
        a = pre_min[k - 1]

        uR = suf_unk[k]
        b = suf_max[k]

        start = b if b > 0 else 1
        limit = a - 1

        if start > limit:
            continue

        cur = pow_table[start][uR]
        exact = cur  # max on right is exactly start
        cnt = exact * pow_table[M - start][uL] % MOD

        prev_cur = cur

        for t in range(start + 1, limit + 1):
            cur = pow_table[t][uR]
            exact = cur - prev_cur
            if exact < 0:
                exact += MOD

            cnt = (cnt + exact * pow_table[M - t][uL]) % MOD
            prev_cur = cur

        ans += cnt
        ans %= MOD

    print(ans % MOD)


if __name__ == "__main__":
    main()