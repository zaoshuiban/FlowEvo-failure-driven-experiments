import sys
from bisect import bisect_left


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    T = int(next(it))
    answers = []
    INF = 10**30

    for _ in range(T):
        N = int(next(it))
        M = int(next(it))
        K = int(next(it))

        destination = N + M
        items = []
        values = [0]

        for _ in range(K):
            x = int(next(it))
            y = int(next(it))
            cost = int(next(it))
            energy = int(next(it))

            s = x + y
            p = s + energy

            items.append((p, s, cost))
            values.append(p)

        if destination <= 0:
            answers.append("0")
            continue

        items.sort()
        values = sorted(set(values))

        index = {v: i for i, v in enumerate(values)}
        size = len(values)

        base = 1
        while base < size:
            base <<= 1

        seg = [INF] * (2 * base)

        def update(pos, val):
            i = pos + base
            if val >= seg[i]:
                return

            seg[i] = val
            i >>= 1

            while i:
                new_val = seg[i << 1]
                if seg[i << 1 | 1] < new_val:
                    new_val = seg[i << 1 | 1]

                if seg[i] == new_val:
                    break

                seg[i] = new_val
                i >>= 1

        def query(left, right):
            result = INF
            left += base
            right += base

            while left < right:
                if left & 1:
                    if seg[left] < result:
                        result = seg[left]
                    left += 1

                if right & 1:
                    right -= 1
                    if seg[right] < result:
                        result = seg[right]

                left >>= 1
                right >>= 1

            return result

        update(index[0], 0)

        answer = INF
        i = 0
        total_items = len(items)

        while i < total_items:
            p = items[i][0]
            j = i
            best = INF

            right_bound = bisect_left(values, p)

            while j < total_items and items[j][0] == p:
                _, s, cost = items[j]
                left_bound = bisect_left(values, s)

                if left_bound < right_bound:
                    current = query(left_bound, right_bound)
                    if current + cost < best:
                        best = current + cost

                j += 1

            if best < INF:
                update(index[p], best)

                if p >= destination and best < answer:
                    answer = best

            i = j

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()