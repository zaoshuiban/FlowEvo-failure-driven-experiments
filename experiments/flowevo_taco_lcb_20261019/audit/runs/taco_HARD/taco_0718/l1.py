import sys
import math


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n, m, a, b = data[idx:idx + 4]
    idx += 4

    ys = data[idx:idx + n]
    idx += n

    zs = data[idx:idx + m]
    idx += m

    lengths = data[idx:idx + m]

    d = b - a
    d2 = d * d
    a2 = a * a

    base = [math.sqrt(a2 + y * y) for y in ys]

    sqrt = math.sqrt

    best_cost = float("inf")
    best_i = -1
    best_j = -1

    def solve(row_l, row_r, opt_l, opt_r):
        nonlocal best_cost, best_i, best_j

        if row_l > row_r:
            return

        mid = (row_l + row_r) // 2
        y = ys[mid]
        base_mid = base[mid]

        row_best_cost = float("inf")
        row_best_col = opt_l

        for j in range(opt_l, opt_r + 1):
            diff = y - zs[j]
            cost = base_mid + sqrt(d2 + diff * diff) + lengths[j]

            if cost < row_best_cost:
                row_best_cost = cost
                row_best_col = j

        if row_best_cost < best_cost:
            best_cost = row_best_cost
            best_i = mid
            best_j = row_best_col

        solve(row_l, mid - 1, opt_l, row_best_col)
        solve(mid + 1, row_r, row_best_col, opt_r)

    solve(0, n - 1, 0, m - 1)

    print(best_i + 1, best_j + 1)


if __name__ == "__main__":
    main()