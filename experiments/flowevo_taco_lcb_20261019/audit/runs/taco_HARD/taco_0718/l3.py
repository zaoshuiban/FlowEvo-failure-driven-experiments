import sys
import math


def main() -> None:
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

    river_width_sq = (b - a) * (b - a)
    a_sq = a * a

    def cmp_value(l1: int, x1: int, l2: int, x2: int) -> int:
        """
        Compares:
            l1 + sqrt(x1)  and  l2 + sqrt(x2)
        Returns:
            -1 if first < second
             0 if equal
             1 if first > second
        Uses exact integer arithmetic.
        """
        d = l2 - l1

        if d == 0:
            if x1 < x2:
                return -1
            if x1 > x2:
                return 1
            return 0

        if d > 0:
            # Need to compare sqrt(x1) with d + sqrt(x2).
            q = x1 - x2 - d * d
            if q < 0:
                return -1

            left = q * q
            right = 4 * d * d * x2

            if left < right:
                return -1
            if left > right:
                return 1
            return 0

        else:
            e = -d
            # Need to compare e + sqrt(x1) with sqrt(x2).
            q = x2 - x1 - e * e
            if q < 0:
                return 1

            left = q * q
            right = 4 * e * e * x1

            if left < right:
                return 1
            if left > right:
                return -1
            return 0

    best_answer = float("inf")
    answer_i = -1
    answer_j = -1

    sqrt = math.sqrt

    def solve(left: int, right: int, opt_left: int, opt_right: int) -> None:
        nonlocal best_answer, answer_i, answer_j

        if left > right:
            return

        mid = (left + right) // 2
        y = ys[mid]

        best_j = opt_left
        best_len = lengths[best_j]

        dy = y - zs[best_j]
        best_dist_sq = river_width_sq + dy * dy

        for j in range(opt_left + 1, opt_right + 1):
            dy = y - zs[j]
            dist_sq = river_width_sq + dy * dy
            cur_len = lengths[j]

            if cmp_value(cur_len, dist_sq, best_len, best_dist_sq) < 0:
                best_j = j
                best_len = cur_len
                best_dist_sq = dist_sq

        total = sqrt(a_sq + y * y) + sqrt(best_dist_sq) + best_len

        if total < best_answer:
            best_answer = total
            answer_i = mid
            answer_j = best_j

        solve(left, mid - 1, opt_left, best_j)
        solve(mid + 1, right, best_j, opt_right)

    solve(0, n - 1, 0, m - 1)

    print(answer_i + 1, answer_j + 1)


if __name__ == "__main__":
    main()