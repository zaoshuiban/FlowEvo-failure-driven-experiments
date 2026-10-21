import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    pts = []
    total = 0
    idx = 1

    for _ in range(n):
        x = data[idx]
        y = data[idx + 1]
        v = data[idx + 2]
        idx += 3
        pts.append((x, y, v))
        total += v

    if n == 1:
        print(0)
        return

    best_diff = total + 1
    best_small = 0

    for i in range(n):
        xi, yi, wi = pts[i]
        vectors = []

        for j in range(n):
            if i == j:
                continue
            xj, yj, wj = pts[j]
            vectors.append((xj - xi, yj - yi, wj))

        for vx, vy, _ in vectors:
            for sign in (1, -1):
                dx = vx * sign
                dy = vy * sign

                current_sum = wi

                for ux, uy, wu in vectors:
                    cross = dx * uy - dy * ux

                    if cross > 0:
                        current_sum += wu
                    elif cross == 0:
                        dot = dx * ux + dy * uy
                        if dot < 0:
                            current_sum += wu

                other_sum = total - current_sum
                diff = abs(current_sum - other_sum)
                smaller = min(current_sum, other_sum)

                if diff < best_diff or (diff == best_diff and smaller > best_small):
                    best_diff = diff
                    best_small = smaller

    print(best_small)


if __name__ == "__main__":
    solve()