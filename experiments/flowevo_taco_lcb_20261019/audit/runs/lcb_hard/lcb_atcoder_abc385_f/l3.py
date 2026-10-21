import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    pos = 1

    hull_x = []
    hull_y = []

    best_num = None
    best_den = 1

    for _ in range(n):
        X = data[pos]
        H = data[pos + 1]
        pos += 2

        if hull_x:
            lo = 0
            hi = len(hull_x) - 1

            # Find the point on the upper hull that minimizes
            # (H - y) / (X - x).
            while lo < hi:
                mid = (lo + hi) // 2

                left = (H - hull_y[mid]) * (X - hull_x[mid + 1])
                right = (H - hull_y[mid + 1]) * (X - hull_x[mid])

                if left <= right:
                    hi = mid
                else:
                    lo = mid + 1

            i = lo
            xi = hull_x[i]
            yi = hull_y[i]

            # Intercept at x = 0 of the line through (xi, yi) and (X, H).
            num = yi * X - H * xi
            den = X - xi

            if best_num is None or num * best_den > best_num * den:
                best_num = num
                best_den = den

        # Maintain the upper convex hull.
        while len(hull_x) >= 2:
            x1, y1 = hull_x[-2], hull_y[-2]
            x2, y2 = hull_x[-1], hull_y[-1]

            cross = (x2 - x1) * (H - y2) - (y2 - y1) * (X - x2)

            if cross >= 0:
                hull_x.pop()
                hull_y.pop()
            else:
                break

        hull_x.append(X)
        hull_y.append(H)

    if best_num is None or best_num < 0:
        print(-1)
        return

    integer_part = best_num // best_den
    remainder = best_num % best_den

    digits = 20
    fractional_part = (remainder * (10 ** digits)) // best_den

    print(f"{integer_part}.{fractional_part:0{digits}d}")


if __name__ == "__main__":
    main()