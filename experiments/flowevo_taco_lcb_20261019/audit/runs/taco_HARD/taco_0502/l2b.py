import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        xs = [next(it) for _ in range(n)]
        ys = [next(it) for _ in range(n)]

        x2s = [2 * x for x in xs]
        y2s = [2 * y for y in ys]
        d2s = [x2s[i] - y2s[i] for i in range(n)]
        s2s = [x2s[i] + y2s[i] for i in range(n)]

        vertical = set(xs)
        horizontal = set(ys)
        diag1 = set(xs[i] - ys[i] for i in range(n))  # x - y = c
        diag2 = set(xs[i] + ys[i] for i in range(n))  # x + y = c

        point_set = set(zip(x2s, y2s))
        candidates = set(point_set)

        v_list = list(vertical)
        h_list = list(horizontal)
        d_list = list(diag1)
        s_list = list(diag2)

        for v in v_list:
            for h in h_list:
                candidates.add((2 * v, 2 * h))

            for d in d_list:
                # x = v, x - y = d -> y = v - d
                candidates.add((2 * v, 2 * (v - d)))

            for s in s_list:
                # x = v, x + y = s -> y = s - v
                candidates.add((2 * v, 2 * (s - v)))

        for h in h_list:
            for d in d_list:
                # y = h, x - y = d -> x = h + d
                candidates.add((2 * (h + d), 2 * h))

            for s in s_list:
                # y = h, x + y = s -> x = s - h
                candidates.add((2 * (s - h), 2 * h))

        for d in d_list:
            for s in s_list:
                # x - y = d, x + y = s
                # 2x = s + d, 2y = s - d
                candidates.add((s + d, s - d))

        ans = 2 * n

        for X2, Y2 in candidates:
            saved = 0

            for i in range(n):
                if (
                    X2 == x2s[i]
                    or Y2 == y2s[i]
                    or X2 - Y2 == d2s[i]
                    or X2 + Y2 == s2s[i]
                ):
                    saved += 1

            if (X2, Y2) in point_set:
                saved += 1

            cost = 2 * n - saved
            if cost < ans:
                ans = cost

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()