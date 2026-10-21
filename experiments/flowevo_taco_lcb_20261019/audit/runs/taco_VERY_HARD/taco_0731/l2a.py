import sys
from bisect import bisect_left


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    T = data[idx]
    idx += 1

    answers = []
    INF = 10**30

    for _ in range(T):
        N = data[idx]
        M = data[idx + 1]
        K = data[idx + 2]
        idx += 3

        target = N + M
        items = []
        coords = [0]

        for _ in range(K):
            x = data[idx]
            y = data[idx + 1]
            c = data[idx + 2]
            e = data[idx + 3]
            idx += 4

            s = x + y
            reach = s + e

            items.append((reach, s, c))
            coords.append(reach)

        if target <= 0:
            answers.append("0")
            continue

        coords = sorted(set(coords))
        n = len(coords)
        bit = [INF] * (n + 1)

        def update(coord_index, value):
            pos = n - coord_index
            while pos <= n:
                if value < bit[pos]:
                    bit[pos] = value
                pos += pos & -pos

        def query_prefix(pos):
            res = INF
            while pos > 0:
                if bit[pos] < res:
                    res = bit[pos]
                pos -= pos & -pos
            return res

        def query_reach_at_least(s):
            coord_index = bisect_left(coords, s)
            return query_prefix(n - coord_index)

        # Initial state: reach = 0, cost = 0
        update(0, 0)

        items.sort()
        ans = INF

        i = 0
        while i < K:
            reach = items[i][0]
            j = i
            best_cost = INF

            while j < K and items[j][0] == reach:
                _, start_needed, cost = items[j]
                previous_cost = query_reach_at_least(start_needed)

                if previous_cost < INF:
                    candidate = previous_cost + cost
                    if candidate < best_cost:
                        best_cost = candidate

                j += 1

            if best_cost < INF:
                coord_index = bisect_left(coords, reach)
                update(coord_index, best_cost)

                if reach >= target and best_cost < ans:
                    ans = best_cost

            i = j

        answers.append(str(ans if ans < INF else -1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()