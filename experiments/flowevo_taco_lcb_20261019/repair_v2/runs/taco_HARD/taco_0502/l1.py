import sys
from collections import Counter

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        X = data[idx:idx + n]
        idx += n

        Y = data[idx:idx + n]
        idx += n

        cnt_h = Counter(Y)       # y = c
        cnt_v = Counter(X)       # x = c
        cnt_dp = Counter()       # y - x = c
        cnt_dm = Counter()       # y + x = c

        point_scaled = set()
        lines = set()

        for x, y in zip(X, Y):
            cnt_dp[y - x] += 1
            cnt_dm[y + x] += 1
            point_scaled.add((2 * x, 2 * y))

            lines.add((0, y))       # horizontal: y = c
            lines.add((1, x))       # vertical: x = c
            lines.add((2, y - x))   # diagonal y - x = c
            lines.add((3, y + x))   # diagonal y + x = c

        candidates = set(point_scaled)
        lines = list(lines)
        m = len(lines)

        # Add all non-parallel line intersections.
        for i in range(m):
            ta, ca = lines[i]
            for j in range(i + 1, m):
                tb, cb = lines[j]

                if ta == tb:
                    continue

                if ta < tb:
                    a, b, c1, c2 = ta, tb, ca, cb
                else:
                    a, b, c1, c2 = tb, ta, cb, ca

                if a == 0:
                    if b == 1:
                        tx = 2 * c2
                        ty = 2 * c1
                    elif b == 2:
                        tx = 2 * (c1 - c2)
                        ty = 2 * c1
                    else:  # b == 3
                        tx = 2 * (c2 - c1)
                        ty = 2 * c1
                elif a == 1:
                    if b == 2:
                        tx = 2 * c1
                        ty = 2 * (c2 + c1)
                    else:  # b == 3
                        tx = 2 * c1
                        ty = 2 * (c2 - c1)
                else:  # a == 2, b == 3
                    tx = c2 - c1
                    ty = c1 + c2

                candidates.add((tx, ty))

        best = 2 * n

        for tx, ty in candidates:
            score = 0

            if ty % 2 == 0:
                score += cnt_h.get(ty // 2, 0)

            if tx % 2 == 0:
                score += cnt_v.get(tx // 2, 0)

            diff = ty - tx
            if diff % 2 == 0:
                score += cnt_dp.get(diff // 2, 0)

            total = ty + tx
            if total % 2 == 0:
                score += cnt_dm.get(total // 2, 0)

            # If the target is exactly one of the given points, it was counted
            # in all four line families, but it should give an extra saving.
            if (tx, ty) in point_scaled:
                score -= 2

            operations = 2 * n - score
            if operations < best:
                best = operations

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()