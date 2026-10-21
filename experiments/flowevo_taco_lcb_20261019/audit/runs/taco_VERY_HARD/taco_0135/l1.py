import sys
from bisect import bisect_right


def build_spf(limit):
    spf = list(range(limit + 1))
    for i in range(2, int(limit ** 0.5) + 1):
        if spf[i] == i:
            for j in range(i * i, limit + 1, i):
                if spf[j] == j:
                    spf[j] = i
    return spf


def solve():
    input_data = sys.stdin.buffer.read().split()
    it = iter(input_data)

    MAX_M = 100000
    spf = build_spf(MAX_M)

    t = int(next(it))
    output = []

    for _ in range(t):
        n = int(next(it))

        menu = [0] * (n + 1)
        prefix = [0] * (n + 1)

        for i in range(1, n + 1):
            val = int(next(it))
            menu[i] = val
            prefix[i] = prefix[i - 1] + val

        q = int(next(it))

        queries_by_p = {}

        for qi in range(q):
            p = int(next(it))
            k = int(next(it))
            queries_by_p.setdefault(p, []).append((k, qi))

        divisible_data = {p: [] for p in queries_by_p}

        for i in range(1, n + 1):
            value = menu[i]
            original_value = value
            last_prime = -1

            while value > 1:
                prime = spf[value]

                if prime != last_prime:
                    if prime in divisible_data:
                        divisible_data[prime].append((i, original_value))
                    last_prime = prime

                while value % prime == 0:
                    value //= prime

        answers = [0] * q

        for p, queries in queries_by_p.items():
            arr = divisible_data[p]

            if not arr:
                for k, qi in queries:
                    answers[qi] = prefix[k]
                continue

            m = len(arr)
            positions = [0] * m
            values = [0] * m

            for i, (pos, val) in enumerate(arr):
                positions[i] = pos
                values[i] = val

            prefix_div_original = [0] * (m + 1)

            for i in range(m):
                prefix_div_original[i + 1] = prefix_div_original[i] + values[i]

            values_desc = sorted(values, reverse=True)
            prefix_top_values = [0] * (m + 1)

            for i in range(m):
                prefix_top_values[i + 1] = prefix_top_values[i] + values_desc[i]

            for k, qi in queries:
                x = bisect_right(positions, k)

                answers[qi] = (
                    prefix[k]
                    - prefix_div_original[x]
                    + prefix_top_values[x]
                )

        output.extend(map(str, answers))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()