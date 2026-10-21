import sys
import math


def exact_less(l1, x1, l2, x2):
    # Returns True iff l1 + sqrt(x1) < l2 + sqrt(x2), exactly.
    d = l2 - l1

    if d >= 0:
        if d == 0:
            return x1 < x2

        a = x1 - x2 - d * d
        if a < 0:
            return True
        return a * a < 4 * d * d * x2
    else:
        e = -d

        if x2 < e * e:
            return False

        a = x2 + e * e - x1
        if a <= 0:
            return False

        return 4 * e * e * x2 < a * a


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m, a, b = data[0:4]
    idx = 4

    ys = data[idx:idx + n]
    idx += n

    zs = data[idx:idx + m]
    idx += m

    lengths = data[idx:idx + m]

    d = b - a
    d2 = d * d
    a2 = a * a

    ans_value = float("inf")
    answer_i = -1
    answer_j = -1

    sqrt = math.sqrt
    EPS = 1e-7

    def solve(left, right, opt_l, opt_r):
        nonlocal ans_value, answer_i, answer_j

        if left > right:
            return

        mid = (left + right) // 2
        y = ys[mid]

        best_j = opt_l
        dy = y - zs[best_j]
        best_x = d2 + dy * dy
        best_l = lengths[best_j]
        best_value = sqrt(best_x) + best_l

        for j in range(opt_l + 1, opt_r + 1):
            dy = y - zs[j]
            x = d2 + dy * dy
            value = sqrt(x) + lengths[j]

            if value < best_value - EPS:
                best_value = value
                best_j = j
                best_x = x
                best_l = lengths[j]
            elif value <= best_value + EPS:
                if exact_less(lengths[j], x, best_l, best_x):
                    best_value = value
                    best_j = j
                    best_x = x
                    best_l = lengths[j]

        total = sqrt(a2 + y * y) + sqrt(best_x) + best_l

        if total < ans_value:
            ans_value = total
            answer_i = mid
            answer_j = best_j

        solve(left, mid - 1, opt_l, best_j)
        solve(mid + 1, right, best_j, opt_r)

    solve(0, n - 1, 0, m - 1)
    print(answer_i + 1, answer_j + 1)


if __name__ == "__main__":
    main()