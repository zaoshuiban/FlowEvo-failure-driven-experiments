import sys
from bisect import bisect_left, bisect_right


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    a = data[2:2 + n]
    a.sort()

    if n == 1:
        print(0)
        return

    pref = [0] * (n + 1)
    total = 0
    for i, value in enumerate(a):
        total += value
        pref[i + 1] = total

    max_a = a[-1]

    # Maximum possible minimum value after at most k operations.
    lo, hi = 0, max_a + k + 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        idx = bisect_left(a, mid)
        cost = mid * idx - pref[idx]
        if cost <= k:
            lo = mid
        else:
            hi = mid - 1
    low = lo

    # Minimum possible maximum value after at most k operations.
    lo, hi = 0, max_a
    while lo < hi:
        mid = (lo + hi) // 2
        idx = bisect_right(a, mid)
        cost = (total - pref[idx]) - mid * (n - idx)
        if cost <= k:
            hi = mid
        else:
            lo = mid + 1
    high = lo

    if low >= high:
        print(0 if total % n == 0 else 1)
    else:
        print(high - low)


if __name__ == "__main__":
    main()