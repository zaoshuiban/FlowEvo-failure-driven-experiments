import sys

def solve():
    MOD = 1_000_000_007

    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = [0] + data[1:1 + n]

    present = bytearray(n + 2)
    for i in range(1, n + 1):
        if a[i] != 0:
            present[a[i]] = 1

    # pref[v] = number of missing values <= v
    pref = [0] * (n + 1)
    missing_count = 0
    for v in range(1, n + 1):
        if present[v] == 0:
            missing_count += 1
        pref[v] = missing_count

    k = missing_count

    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i % MOD

    fact_k = fact[k]
    fact_km1 = fact[k - 1] if k >= 1 else 0
    fact_km2 = fact[k - 2] if k >= 2 else 0
    missing_pairs = (k * (k - 1) // 2) % MOD if k >= 2 else 0

    bit = [0] * (n + 2)

    ans = 0
    zero_right = 0
    sum_fixed_h = 0

    for i in range(n, 0, -1):
        w = a[i]
        weight = fact[n - i]

        if w == 0:
            # Zero position.
            s = 0

            if k >= 1:
                s = fact_km1 * sum_fixed_h % MOD

            if k >= 2:
                s += zero_right * fact_km2 % MOD * missing_pairs
                s %= MOD

            ans = (ans + weight * s) % MOD
            zero_right += 1

        else:
            # Fixed position. Count fixed smaller values to the right.
            idx = w - 1
            smaller_fixed_right = 0
            while idx > 0:
                smaller_fixed_right += bit[idx]
                idx -= idx & -idx

            missing_smaller = pref[w - 1]

            s = fact_k * smaller_fixed_right % MOD

            if k >= 1:
                s += fact_km1 * zero_right % MOD * missing_smaller
                s %= MOD

            ans = (ans + weight * s) % MOD

            # Add current fixed value to Fenwick tree.
            idx = w
            while idx <= n:
                bit[idx] += 1
                idx += idx & -idx

            # h(w) = number of missing values greater than w
            h = k - pref[w]
            sum_fixed_h += h

    result = (fact_k + ans) % MOD
    print(result)


if __name__ == "__main__":
    solve()