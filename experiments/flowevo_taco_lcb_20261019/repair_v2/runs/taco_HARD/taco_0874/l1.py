import sys
from itertools import product


def is_square(points):
    distances = []
    for i in range(4):
        x1, y1 = points[i]
        for j in range(i + 1, 4):
            x2, y2 = points[j]
            dx = x1 - x2
            dy = y1 - y2
            distances.append(dx * dx + dy * dy)

    distances.sort()
    side = distances[0]

    return (
        side > 0
        and distances[1] == side
        and distances[2] == side
        and distances[3] == side
        and distances[4] == 2 * side
        and distances[5] == 2 * side
    )


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    idx = 1

    answers = []

    for _ in range(n):
        moles = []

        for _ in range(4):
            x, y, a, b = data[idx], data[idx + 1], data[idx + 2], data[idx + 3]
            idx += 4

            positions = []
            cx, cy = x, y

            for _ in range(4):
                positions.append((cx, cy))
                cx, cy = a + b - cy, b + cx - a

            moles.append(positions)

        best = 10**9

        for rotations in product(range(4), repeat=4):
            points = [
                moles[0][rotations[0]],
                moles[1][rotations[1]],
                moles[2][rotations[2]],
                moles[3][rotations[3]],
            ]

            if is_square(points):
                best = min(best, sum(rotations))

        answers.append(str(best if best != 10**9 else -1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()