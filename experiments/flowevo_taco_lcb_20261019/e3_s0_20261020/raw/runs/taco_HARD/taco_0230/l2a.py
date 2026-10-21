import sys
from bisect import bisect_left, bisect_right

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]
    a.sort()

    prefix = [0] * (n + 1)
    total = 0
    for i, x in enumerate(a, 1):
        total += x
        prefix[i] = total

    floor_avg = total // n
    ceil_avg = (total + n - 1) // n

    # Maximum possible final minimum
    lo, hi = a[0], floor_avg
    while lo < hi:
        mid = (lo + hi + 1) // 2
        idx = bisect_left(a, mid)
        cost = idx * mid - prefix[idx]

        if cost <= k:
            lo = mid
        else:
            hi = mid - 1

    final_min = lo

    # Minimum possible final maximum
    lo, hi = ceil_avg, a[-1]
    while lo < hi:
        mid = (lo + hi) // 2
        idx = bisect_right(a, mid)
        count = n - idx
        cost = (total - prefix[idx]) - count * mid

        if cost <= k:
            hi = mid
        else:
            lo = mid + 1

    final_max = lo

    print(final_max - final_min)


if __name__ == "__main__":
    solve()