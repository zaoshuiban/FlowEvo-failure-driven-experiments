import sys

MAXA = 100000

# Smallest prime factor sieve
spf = list(range(MAXA + 1))
for i in range(2, 317):
    if spf[i] == i:
        for j in range(i * i, MAXA + 1, i):
            if spf[j] == j:
                spf[j] = i


def fast_ints():
    data = sys.stdin.buffer.read()
    num = 0
    in_num = False

    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            in_num = True
        elif in_num:
            yield num
            num = 0
            in_num = False

    if in_num:
        yield num


def solve():
    it = iter(fast_ints())

    try:
        T = next(it)
    except StopIteration:
        return

    output = []

    for _ in range(T):
        N = next(it)

        A = [0] * N
        pref = [0] * (N + 1)

        for i in range(N):
            x = next(it)
            A[i] = x
            pref[i + 1] = pref[i] + x

        Q = next(it)

        groups = {}
        needed = set()

        for qi in range(Q):
            p = next(it)
            k = next(it)

            groups.setdefault(p, []).append((k, qi))
            needed.add(p)

        ans = [0] * Q

        occ_pos = {}
        occ_val = {}

        for i, x in enumerate(A, 1):
            v = x

            while v > 1:
                p = spf[v]

                if p in needed:
                    if p not in occ_pos:
                        occ_pos[p] = [i]
                        occ_val[p] = [x]
                    else:
                        occ_pos[p].append(i)
                        occ_val[p].append(x)

                while v % p == 0:
                    v //= p

        for p, queries in groups.items():
            positions = occ_pos.get(p)

            if positions is None:
                for k, qi in queries:
                    ans[qi] = pref[k]
                continue

            values = occ_val[p]

            sorted_values = sorted(values, reverse=True)

            m = len(values)
            top_pref = [0] * (m + 1)

            running = 0
            for j in range(m):
                running += sorted_values[j]
                top_pref[j + 1] = running

            queries.sort(key=lambda item: item[0])

            ptr = 0
            original_sum = 0

            for k, qi in queries:
                while ptr < m and positions[ptr] <= k:
                    original_sum += values[ptr]
                    ptr += 1

                ans[qi] = pref[k] - original_sum + top_pref[ptr]

        output.extend(map(str, ans))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()