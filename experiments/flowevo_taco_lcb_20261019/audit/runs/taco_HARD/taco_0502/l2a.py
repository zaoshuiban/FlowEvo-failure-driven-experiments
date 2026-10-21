import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    answers = []

    for _ in range(T):
        n = next(it)
        xs = [next(it) for _ in range(n)]
        ys = [next(it) for _ in range(n)]

        points = []
        lines = set()

        for x, y in zip(xs, ys):
            points.append((2 * x, 2 * y, 2 * (x + y), 2 * (x - y)))

            # x = x
            lines.add((1, 0, x))
            # y = y
            lines.add((0, 1, y))
            # x + y = constant
            lines.add((1, 1, x + y))
            # x - y = constant
            lines.add((1, -1, x - y))

        candidates = set()
        for px, py, _, _ in points:
            candidates.add((px, py))

        lines = list(lines)
        m = len(lines)

        for i in range(m):
            a1, b1, c1 = lines[i]
            for j in range(i + 1, m):
                a2, b2, c2 = lines[j]

                det = a1 * b2 - a2 * b1
                if det == 0:
                    continue

                x_num = c1 * b2 - c2 * b1
                y_num = a1 * c2 - a2 * c1

                # Store coordinates multiplied by 2.
                qx2 = (2 * x_num) // det
                qy2 = (2 * y_num) // det
                candidates.add((qx2, qy2))

        best_score = 0
        max_possible_score = n + 1

        for qx, qy in candidates:
            qsum = qx + qy
            qdiff = qx - qy
            score = 0

            for px, py, psum, pdiff in points:
                if qx == px:
                    if qy == py:
                        score += 2
                    else:
                        score += 1
                elif qy == py or qsum == psum or qdiff == pdiff:
                    score += 1

            if score > best_score:
                best_score = score
                if best_score == max_possible_score:
                    break

        answers.append(str(2 * n - best_score))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()