import sys
from bisect import bisect_left

INF = 10**30


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    answers = []

    for _ in range(T):
        N = next(it)
        M = next(it)
        K = next(it)

        batteries = []
        reach_values = [0]

        for _ in range(K):
            x = next(it)
            y = next(it)
            c = next(it)
            e = next(it)

            s = x + y
            reach = s + e
            batteries.append((s, reach, c))
            reach_values.append(reach)

        target_sum = N + M

        batteries.sort(key=lambda item: item[0])

        values = sorted(set(reach_values))
        nvals = len(values)

        size = 1
        while size < nvals:
            size <<= 1

        seg = [INF] * (2 * size)

        def update(pos: int, val: int) -> None:
            idx = pos + size
            if val >= seg[idx]:
                return
            seg[idx] = val
            idx >>= 1
            while idx:
                seg[idx] = min(seg[idx << 1], seg[idx << 1 | 1])
                idx >>= 1

        def query_from(left: int) -> int:
            if left >= nvals:
                return INF

            l = left + size
            r = nvals + size
            res = INF

            while l < r:
                if l & 1:
                    res = min(res, seg[l])
                    l += 1
                if r & 1:
                    r -= 1
                    res = min(res, seg[r])
                l >>= 1
                r >>= 1

            return res

        source_pos = bisect_left(values, 0)
        update(source_pos, 0)

        for s, reach, cost in batteries:
            left = bisect_left(values, s)
            base_cost = query_from(left)

            if base_cost < INF:
                new_cost = base_cost + cost
                pos = bisect_left(values, reach)
                update(pos, new_cost)

        target_pos = bisect_left(values, target_sum)
        answers.append(str(query_from(target_pos)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()