import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    points = []
    idx = 1

    for _ in range(n):
        x = data[idx]
        y = data[idx + 1]
        v = data[idx + 2]
        idx += 3
        points.append((x, y, v))

    total = sum(v for _, _, v in points)
    answer = 0

    for i in range(n):
        xi, yi, vi = points[i]

        for j in range(n):
            if i == j:
                continue

            xj, yj, vj = points[j]
            dx = xj - xi
            dy = yj - yi

            base_weight = 0

            for k in range(n):
                if k == i or k == j:
                    continue

                xk, yk, vk = points[k]
                cross = dx * (yk - yi) - dy * (xk - xi)

                if cross > 0:
                    base_weight += vk

            for added in (0, vi, vj, vi + vj):
                left_weight = base_weight + added
                right_weight = total - left_weight
                smaller = min(left_weight, right_weight)

                if smaller > answer:
                    answer = smaller

    print(answer)


if __name__ == "__main__":
    main()