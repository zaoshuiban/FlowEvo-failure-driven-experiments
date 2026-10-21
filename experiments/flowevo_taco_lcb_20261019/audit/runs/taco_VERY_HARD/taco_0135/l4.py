import sys


def build_spf(n: int):
    """Smallest prime factor for every number up to n."""
    spf = list(range(n + 1))
    if n >= 1:
        spf[1] = 1

    i = 2
    while i * i <= n:
        if spf[i] == i:
            for j in range(i * i, n + 1, i):
                if spf[j] == j:
                    spf[j] = i
        i += 1

    return spf


def distinct_prime_factors(x: int, spf):
    factors = []
    while x > 1:
        p = spf[x]
        factors.append(p)
        while x % p == 0:
            x //= p
    return factors


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]

    # First pass: find maximum M_i so that we can build SPF dynamically.
    idx = 1
    max_m = 1

    for _ in range(t):
        n = data[idx]
        idx += 1

        for j in range(n):
            if data[idx + j] > max_m:
                max_m = data[idx + j]
        idx += n

        q = data[idx]
        idx += 1
        idx += 2 * q

    spf = build_spf(max_m)
    factor_cache = {}

    out = []
    idx = 1

    for _ in range(t):
        n = data[idx]
        idx += 1

        m = data[idx:idx + n]
        idx += n

        q = data[idx]
        idx += 1

        groups = {}
        for qi in range(q):
            p = data[idx]
            k = data[idx + 1]
            idx += 2
            groups.setdefault(p, []).append((k, qi))

        pref = [0] * (n + 1)
        for i, value in enumerate(m, 1):
            pref[i] = pref[i - 1] + value

        occ_pos = {}
        occ_val = {}

        for i, value in enumerate(m, 1):
            factors = factor_cache.get(value)
            if factors is None:
                factors = distinct_prime_factors(value, spf)
                factor_cache[value] = factors

            for p in factors:
                if p in groups:
                    if p in occ_pos:
                        occ_pos[p].append(i)
                        occ_val[p].append(value)
                    else:
                        occ_pos[p] = [i]
                        occ_val[p] = [value]

        ans = [0] * q

        for p, queries in groups.items():
            positions = occ_pos.get(p)

            if positions is None:
                for k, qi in queries:
                    ans[qi] = pref[k]
                continue

            values = occ_val[p]
            sorted_values = sorted(values, reverse=True)

            size = len(values)
            top_pref = [0] * (size + 1)

            running = 0
            for i, value in enumerate(sorted_values, 1):
                running += value
                top_pref[i] = running

            queries.sort(key=lambda item: item[0])

            ptr = 0
            original_sum = 0

            for k, qi in queries:
                while ptr < size and positions[ptr] <= k:
                    original_sum += values[ptr]
                    ptr += 1

                ans[qi] = pref[k] - original_sum + top_pref[ptr]

        out.extend(map(str, ans))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()