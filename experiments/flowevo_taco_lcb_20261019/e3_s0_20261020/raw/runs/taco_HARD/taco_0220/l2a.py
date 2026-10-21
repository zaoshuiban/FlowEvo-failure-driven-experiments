import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    arr = data[1:1 + 2 * n]

    positions = {}
    for i, value in enumerate(arr):
        positions.setdefault(value, []).append(i)

    values = list(positions.keys())
    freqs = [len(positions[v]) for v in values]
    m = len(values)

    # dp[used][d1] = maximum d2 after processing some values,
    # where used cubes are in heap 1 and d1 distinct values are in heap 1.
    # d2 is the number of distinct values in heap 2.
    D = m + 1
    N = n + 1

    init = [[-1] * D for _ in range(N)]
    init[0][0] = 0
    layers = [init]

    prefix = 0

    for idx in range(m):
        f = freqs[idx]
        prev = layers[-1]
        cur = [[-1] * D for _ in range(N)]
        prefix += f

        for used in range(N):
            row = prev[used]
            for d1 in range(m + 1):
                d2 = row[d1]
                if d2 < 0:
                    continue

                # Put all cubes of this value into heap 1.
                nu = used + f
                if nu <= n and d1 + 1 <= m and prefix - nu <= n:
                    if d2 > cur[nu][d1 + 1]:
                        cur[nu][d1 + 1] = d2

                # Put all cubes of this value into heap 2.
                if prefix - used <= n:
                    nd2 = d2 + 1
                    if nd2 <= m and nd2 > cur[used][d1]:
                        cur[used][d1] = nd2

                # Split this value between both heaps.
                if f >= 2 and d1 + 1 <= m:
                    nd2 = d2 + 1
                    if nd2 <= m:
                        low = max(1, prefix - n - used)
                        high = min(f - 1, n - used)

                        for x in range(low, high + 1):
                            nu = used + x
                            if nd2 > cur[nu][d1 + 1]:
                                cur[nu][d1 + 1] = nd2

        layers.append(cur)

    final = layers[-1]

    best = -1
    best_d1 = 0
    best_d2 = 0

    for d1 in range(m + 1):
        d2 = final[n][d1]
        if d2 >= 0:
            product = d1 * d2
            if product > best:
                best = product
                best_d1 = d1
                best_d2 = d2

    actions = [None] * m
    used = n
    d1 = best_d1
    d2 = best_d2

    # Reconstruct one optimal partition.
    for idx in range(m - 1, -1, -1):
        f = freqs[idx]
        prev = layers[idx]
        found = False

        # This value was entirely in heap 1.
        if not found and d1 >= 1 and used >= f:
            pu = used - f
            pd1 = d1 - 1
            if 0 <= pu <= n and 0 <= pd1 <= m and prev[pu][pd1] == d2:
                actions[idx] = ('1', 0)
                used = pu
                d1 = pd1
                found = True

        # This value was entirely in heap 2.
        if not found and d2 >= 1:
            pu = used
            pd1 = d1
            pd2 = d2 - 1
            if 0 <= pu <= n and 0 <= pd1 <= m and prev[pu][pd1] == pd2:
                actions[idx] = ('2', 0)
                d2 = pd2
                found = True

        # This value was split between the two heaps.
        if not found and f >= 2 and d1 >= 1 and d2 >= 1:
            pd1 = d1 - 1
            pd2 = d2 - 1

            for x in range(1, f):
                pu = used - x
                if 0 <= pu <= n and prev[pu][pd1] == pd2:
                    actions[idx] = ('s', x)
                    used = pu
                    d1 = pd1
                    d2 = pd2
                    found = True
                    break

    answer = [0] * (2 * n)

    for idx, value in enumerate(values):
        indices = positions[value]
        action, x = actions[idx]

        if action == '1':
            for p in indices:
                answer[p] = 1
        elif action == '2':
            for p in indices:
                answer[p] = 2
        else:
            for j, p in enumerate(indices):
                answer[p] = 1 if j < x else 2

    sys.stdout.write(str(best) + "\n")
    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    solve()