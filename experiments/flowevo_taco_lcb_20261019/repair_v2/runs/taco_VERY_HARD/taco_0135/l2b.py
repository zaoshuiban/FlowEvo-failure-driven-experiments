import sys

MAXA = 100000

# Smallest prime factor sieve
spf = list(range(MAXA + 1))
for i in range(2, int(MAXA ** 0.5) + 1):
    if spf[i] == i:
        for j in range(i * i, MAXA + 1, i):
            if spf[j] == j:
                spf[j] = i


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    T = next(it)
    output = []

    for _ in range(T):
        N = next(it)

        pref = [0] * (N + 1)
        divisors = {}

        for i in range(1, N + 1):
            x = next(it)
            pref[i] = pref[i - 1] + x

            v = x
            while v > 1:
                p = spf[v]

                if p in divisors:
                    divisors[p].append((i, x))
                else:
                    divisors[p] = [(i, x)]

                while v % p == 0:
                    v //= p

        Q = next(it)

        query_groups = {}
        for qi in range(Q):
            p = next(it)
            k = next(it)
            query_groups.setdefault(p, []).append((qi, k))

        ans = [0] * Q

        for p, queries in query_groups.items():
            entries = divisors.get(p)

            if entries is None:
                for qi, k in queries:
                    ans[qi] = pref[k]
                continue

            count = len(entries)

            # Values of dishes divisible by p, sorted descending,
            # then converted into prefix sums.
            top_values = [0] * count
            for j in range(count):
                top_values[j] = entries[j][1]

            top_values.sort(reverse=True)

            running = 0
            for j in range(count):
                running += top_values[j]
                top_values[j] = running

            queries.sort(key=lambda x: x[1])

            ptr = 0
            eligible_prefix_sum = 0

            for qi, k in queries:
                while ptr < count and entries[ptr][0] <= k:
                    eligible_prefix_sum += entries[ptr][1]
                    ptr += 1

                top_sum = top_values[ptr - 1] if ptr > 0 else 0
                ans[qi] = pref[k] - eligible_prefix_sum + top_sum

        output.extend(map(str, ans))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()