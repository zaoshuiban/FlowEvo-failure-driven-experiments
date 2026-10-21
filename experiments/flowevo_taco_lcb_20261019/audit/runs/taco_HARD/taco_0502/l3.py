import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        xs = [next(it) for _ in range(n)]
        ys = [next(it) for _ in range(n)]

        diff = [xs[i] - ys[i] for i in range(n)]
        summ = [xs[i] + ys[i] for i in range(n)]

        mask_x = {}
        mask_y = {}
        mask_d = {}
        mask_s = {}

        for i in range(n):
            bit = 1 << i

            v = xs[i]
            mask_x[v] = mask_x.get(v, 0) | bit

            v = ys[i]
            mask_y[v] = mask_y.get(v, 0) | bit

            v = diff[i]
            mask_d[v] = mask_d.get(v, 0) | bit

            v = summ[i]
            mask_s[v] = mask_s.get(v, 0) | bit

        point_set = set()
        for i in range(n):
            point_set.add((2 * xs[i], 2 * ys[i]))

        x_values = set(xs)
        y_values = set(ys)
        d_values = set(diff)
        s_values = set(summ)

        candidates = set(point_set)

        for x in x_values:
            X2 = 2 * x

            for y in y_values:
                candidates.add((X2, 2 * y))

            for d in d_values:
                candidates.add((X2, 2 * (x - d)))

            for s in s_values:
                candidates.add((X2, 2 * (s - x)))

        for y in y_values:
            Y2 = 2 * y

            for d in d_values:
                candidates.add((2 * (y + d), Y2))

            for s in s_values:
                candidates.add((2 * (s - y), Y2))

        for d in d_values:
            for s in s_values:
                candidates.add((d + s, s - d))

        best_saved = 0

        for X2, Y2 in candidates:
            covered_mask = 0

            if X2 % 2 == 0:
                covered_mask |= mask_x.get(X2 // 2, 0)

            if Y2 % 2 == 0:
                covered_mask |= mask_y.get(Y2 // 2, 0)

            diff2 = X2 - Y2
            if diff2 % 2 == 0:
                covered_mask |= mask_d.get(diff2 // 2, 0)

            sum2 = X2 + Y2
            if sum2 % 2 == 0:
                covered_mask |= mask_s.get(sum2 // 2, 0)

            saved = covered_mask.bit_count()

            if (X2, Y2) in point_set:
                saved += 1

            if saved > best_saved:
                best_saved = saved

        answers.append(str(2 * n - best_saved))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()