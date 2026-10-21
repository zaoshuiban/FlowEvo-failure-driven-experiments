import sys
from bisect import bisect_left


def int_gen():
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
    it = int_gen()
    try:
        t = next(it)
    except StopIteration:
        return

    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)

        total_elements = n * n
        a = [next(it) for _ in range(total_elements)]
        a.sort()

        # Position of the median inside a sorted row, 1-indexed.
        p = n // 2 + 1

        # Number of elements from the median to the end of a row.
        r = n - p + 1

        # To have all medians >= G, at least n*r elements must be >= G.
        max_l = total_elements - n * r

        low_indices = [p * i - 1 for i in range(1, n + 1)]

        def minimum_cost_with_goodness_at_least(g):
            l = bisect_left(a, g)

            if l > max_l:
                return k + 1

            cost = 0

            for i, low_idx in enumerate(low_indices):
                idx = low_idx
                forced_idx = l + i
                if forced_idx > idx:
                    idx = forced_idx

                cost += a[idx]
                if cost > k:
                    return cost

            return cost

        lo = 0
        hi = total_elements - 1
        answer = -1

        while lo <= hi:
            mid = (lo + hi) // 2
            g = a[mid]

            if minimum_cost_with_goodness_at_least(g) <= k:
                answer = g
                lo = mid + 1
            else:
                hi = mid - 1

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()