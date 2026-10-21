import sys
from math import gcd


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    xs = [0] * n
    ys = [0] * n

    idx = 1
    for i in range(n):
        xs[i] = data[idx]
        ys[i] = data[idx + 1]
        idx += 2

    # Precompute normalized direction keys for all possible coordinate differences.
    R = 200
    size = 2 * R + 1
    key_map = [[0] * size for _ in range(size)]

    for dx in range(-R, R + 1):
        for dy in range(-R, R + 1):
            if dx == 0 and dy == 0:
                continue

            g = gcd(abs(dx), abs(dy))
            ax = dx // g
            ay = dy // g

            # Treat a line as undirected: normalize sign.
            if ax < 0 or (ax == 0 and ay < 0):
                ax = -ax
                ay = -ay

            key_map[dx + R][dy + R] = ax * 401 + (ay + 200)

    total_triangles = n * (n - 1) * (n - 2) // 6
    collinear_pair_sum = 0

    for i in range(n):
        xi = xs[i]
        yi = ys[i]
        counts = {}

        for j in range(n):
            if i == j:
                continue

            dx = xs[j] - xi + R
            dy = ys[j] - yi + R
            key = key_map[dx][dy]

            previous = counts.get(key, 0)
            collinear_pair_sum += previous
            counts[key] = previous + 1

    collinear_triangles = collinear_pair_sum // 3
    print(total_triangles - collinear_triangles)


if __name__ == "__main__":
    solve()