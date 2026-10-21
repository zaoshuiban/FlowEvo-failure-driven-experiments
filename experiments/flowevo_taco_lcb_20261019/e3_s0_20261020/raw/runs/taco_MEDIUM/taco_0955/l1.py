import sys

MOD = 1_000_000_007
DIRECT_OP = 200_000
POW_OP = 5_000


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    max_n = max(data)

    # Euler's totient
    phi = list(range(max_n + 1))
    if max_n >= 1:
        phi[1] = 1

    for i in range(2, max_n + 1):
        if phi[i] == i:
            for j in range(i, max_n + 1, i):
                phi[j] -= phi[j] // i

    # Prefix sums of phi
    pref_phi = [0] * (max_n + 1)
    s = 0
    for i in range(1, max_n + 1):
        s += phi[i]
        if s >= MOD:
            s %= MOD
        pref_phi[i] = s

    # Modular inverses
    inv = [0] * (max_n + 2)
    inv[1] = 1
    for i in range(2, max_n + 2):
        inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD

    pos = 1
    answers = []

    for _ in range(t):
        k = data[pos]
        pos += 1

        dims = data[pos:pos + k]
        pos += k

        min_n = min(dims)

        cnt = {}
        for v in dims:
            cnt[v] = cnt.get(v, 0) + 1

        groups = list(cnt.items())
        distinct = len(groups)
        multi_count = sum(1 for _, c in groups if c > 1)

        # Direct computation for small cases
        if distinct * min_n <= DIRECT_OP and min_n * multi_count <= POW_OP:
            ans = 0
            for d in range(1, min_n + 1):
                prod = 1
                for v, c in groups:
                    q = v // d
                    if c == 1:
                        prod = prod * q % MOD
                    else:
                        prod = prod * pow(q, c, MOD) % MOD
                ans += phi[d] * prod
            answers.append(str(ans % MOD))
            continue

        # Event-based computation
        init_product = 1
        events = []

        for v, c in groups:
            if c == 1:
                init_product = init_product * v % MOD
            else:
                init_product = init_product * pow(v, c, MOD) % MOD

            if min_n >= 2:
                q = v  # floor(v / 1)
                while True:
                    end = v // q
                    if end >= min_n:
                        break

                    nxt = end + 1
                    new_q = v // nxt

                    factor = new_q * inv[q] % MOD
                    if c != 1:
                        factor = pow(factor, c, MOD)

                    events.append(nxt * MOD + factor)
                    q = new_q

        event_count = len(events)

        if event_count == 0:
            ans = (pref_phi[min_n] - pref_phi[0]) * init_product % MOD
            answers.append(str(ans))
            continue

        # Choose between sorting events and bucketing them
        use_sorted = event_count * event_count.bit_length() < min_n * 8

        if use_sorted:
            events.sort()

            prod = init_product
            current = 1
            ans = 0
            idx = 0

            while idx < event_count:
                start = events[idx] // MOD
                if start > min_n:
                    break

                if start > current:
                    ans += (pref_phi[start - 1] - pref_phi[current - 1]) * prod
                    current = start

                factor_at_start = 1

                while idx < event_count:
                    code = events[idx]
                    event_start = code // MOD
                    if event_start != start:
                        break

                    factor = code - event_start * MOD
                    factor_at_start = factor_at_start * factor % MOD
                    idx += 1

                prod = prod * factor_at_start % MOD

            if current <= min_n:
                ans += (pref_phi[min_n] - pref_phi[current - 1]) * prod

            answers.append(str(ans % MOD))

        else:
            event_product = [1] * (min_n + 2)

            for code in events:
                start = code // MOD
                factor = code - start * MOD
                event_product[start] = event_product[start] * factor % MOD

            prod = init_product
            ans = 0

            for d in range(1, min_n + 1):
                factor = event_product[d]
                if factor != 1:
                    prod = prod * factor % MOD

                ans += phi[d] * prod

            answers.append(str(ans % MOD))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()