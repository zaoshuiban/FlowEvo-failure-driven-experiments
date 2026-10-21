import sys
from collections import Counter


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    arr = data[1:1 + 2 * n]

    counter = Counter(arr)
    values = list(counter.keys())
    counts = [counter[v] for v in values]
    m = len(values)

    # dp[u][a] = maximum number of distinct values in the second heap,
    # after processing some values, where:
    # u = number of cubes put into the first heap,
    # a = number of distinct values in the first heap.
    prev = [[-1] * (m + 1) for _ in range(n + 1)]
    prev[0][0] = 0
    layers = [prev]

    for c in counts:
        cur = [[-1] * (m + 1) for _ in range(n + 1)]

        for u in range(n + 1):
            row = prev[u]
            for a, d2 in enumerate(row):
                if d2 < 0:
                    continue

                # Put all c copies into the second heap.
                if d2 + 1 > cur[u][a]:
                    cur[u][a] = d2 + 1

                # Put all c copies into the first heap.
                if u + c <= n and a + 1 <= m:
                    if d2 > cur[u + c][a + 1]:
                        cur[u + c][a + 1] = d2

                # Split copies between both heaps.
                if c >= 2 and a + 1 <= m:
                    nd = d2 + 1
                    max_x = min(c - 1, n - u)
                    for x in range(1, max_x + 1):
                        if nd > cur[u + x][a + 1]:
                            cur[u + x][a + 1] = nd

        prev = cur
        layers.append(cur)

    best = -1
    best_a = 0
    best_b = 0

    for a in range(m + 1):
        b = prev[n][a]
        if b >= 0:
            prod = a * b
            if prod > best:
                best = prod
                best_a = a
                best_b = b

    # Reconstruct how many copies of each value go to the first heap.
    xval = [0] * m
    u = n
    a = best_a
    b = best_b

    for idx in range(m - 1, -1, -1):
        c = counts[idx]
        pre = layers[idx]
        max_x = min(c, u)

        for x in range(max_x + 1):
            da = 1 if x > 0 else 0
            db = 1 if x < c else 0

            if a - da < 0 or b - db < 0:
                continue

            if pre[u - x][a - da] == b - db:
                xval[idx] = x
                u -= x
                a -= da
                b -= db
                break

    remaining = {values[i]: xval[i] for i in range(m)}

    labels = []
    for v in arr:
        if remaining.get(v, 0) > 0:
            labels.append('1')
            remaining[v] -= 1
        else:
            labels.append('2')

    sys.stdout.write(str(best) + "\n" + " ".join(labels) + "\n")


if __name__ == "__main__":
    solve()