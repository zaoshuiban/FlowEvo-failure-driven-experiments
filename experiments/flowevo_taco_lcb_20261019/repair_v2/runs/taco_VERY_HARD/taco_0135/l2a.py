import sys
from bisect import bisect_right

MAXA = 100000

# Smallest prime factor sieve
spf = list(range(MAXA + 1))
for i in range(2, int(MAXA ** 0.5) + 1):
    if spf[i] == i:
        for j in range(i * i, MAXA + 1, i):
            if spf[j] == j:
                spf[j] = i


def main():
    tokens = list(map(int, sys.stdin.buffer.read().split()))
    if not tokens:
        return

    it = iter(tokens)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        m = [next(it) for _ in range(n)]

        prefix = [0] * (n + 1)
        curr_sum = 0
        for i, val in enumerate(m, 1):
            curr_sum += val
            prefix[i] = curr_sum

        positions = {}
        occurrence_values = {}

        for idx, val in enumerate(m, 1):
            x = val
            while x > 1:
                p = spf[x]

                if p in positions:
                    positions[p].append(idx)
                    occurrence_values[p].append(val)
                else:
                    positions[p] = [idx]
                    occurrence_values[p] = [val]

                while x % p == 0:
                    x //= p

        prepared = {}

        for p, pos in positions.items():
            vals = occurrence_values[p]
            size = len(vals)

            pref_occ = [0] * (size + 1)
            s = 0
            for i, v in enumerate(vals, 1):
                s += v
                pref_occ[i] = s

            top_vals = sorted(vals, reverse=True)
            pref_top = [0] * (size + 1)
            s = 0
            for i, v in enumerate(top_vals, 1):
                s += v
                pref_top[i] = s

            prepared[p] = (pos, pref_occ, pref_top)

        q = next(it)

        for _ in range(q):
            p = next(it)
            k = next(it)

            data = prepared.get(p)

            if data is None:
                answers.append(str(prefix[k]))
            else:
                pos, pref_occ, pref_top = data
                count = bisect_right(pos, k)

                result = prefix[k] - pref_occ[count] + pref_top[count]
                answers.append(str(result))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()