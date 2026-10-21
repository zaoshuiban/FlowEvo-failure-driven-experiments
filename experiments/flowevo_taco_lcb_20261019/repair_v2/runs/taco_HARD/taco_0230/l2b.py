import sys
from bisect import bisect_left, bisect_right


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]
    a.sort()

    prefix = [0] * (n + 1)
    total = 0
    for i, value in enumerate(a, 1):
        total += value
        prefix[i] = total

    # Find the maximum possible final minimum.
    left = a[0]
    right = total // n
    min_value = left

    while left <= right:
        mid = (left + right) // 2
        idx = bisect_left(a, mid)
        cost = mid * idx - prefix[idx]

        if cost <= k:
            min_value = mid
            left = mid + 1
        else:
            right = mid - 1

    # Find the minimum possible final maximum.
    left = (total + n - 1) // n
    right = a[-1]
    max_value = right

    while left <= right:
        mid = (left + right) // 2
        idx = bisect_right(a, mid)
        cost = (total - prefix[idx]) - mid * (n - idx)

        if cost <= k:
            max_value = mid
            right = mid - 1
        else:
            left = mid + 1

    print(max_value - min_value)


if __name__ == "__main__":
    main()