import sys
import math


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m, a, b = data[0], data[1], data[2], data[3]
    pos = 4

    A = data[pos:pos + n]
    pos += n

    B = data[pos:pos + m]
    pos += m

    L = data[pos:pos + m]

    d = b - a
    d2 = d * d
    a2 = a * a
    sqrt = math.sqrt

    first = [sqrt(a2 + y * y) for y in A]

    best_value = float("inf")
    best_i = best_j = -1

    for j, z in enumerate(B):
        lo, hi = 0, n - 1

        while lo < hi:
            mid = (lo + hi) // 2

            y1 = A[mid]
            y2 = A[mid + 1]

            dy1 = z - y1
            dy2 = z - y2

            cost1 = first[mid] + sqrt(d2 + dy1 * dy1)
            cost2 = first[mid + 1] + sqrt(d2 + dy2 * dy2)

            if cost1 <= cost2:
                hi = mid
            else:
                lo = mid + 1

        i = lo
        dy = z - A[i]
        total = first[i] + sqrt(d2 + dy * dy) + L[j]

        if total < best_value:
            best_value = total
            best_i = i + 1
            best_j = j + 1

    print(best_i, best_j)


if __name__ == "__main__":
    main()