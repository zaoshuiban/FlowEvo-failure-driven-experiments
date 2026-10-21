import sys
from math import isqrt

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    total = sum(a)

    if total < 2:
        print(-1)
        return

    pos = [i for i, x in enumerate(a) if x]
    pref = [0] * (total + 1)

    for i, p in enumerate(pos):
        pref[i + 1] = pref[i] + p

    divisors = []
    for d in range(2, isqrt(total) + 1):
        if total % d == 0:
            divisors.append(d)
            if d * d != total:
                divisors.append(total // d)
    divisors.append(total)

    ans = 10**30

    for k in set(divisors):
        cost = 0

        for left in range(0, total, k):
            right = left + k
            mid = left + k // 2

            left_count = mid - left
            cost += pos[mid] * left_count - (pref[mid] - pref[left])

            right_count = right - mid - 1
            cost += (pref[right] - pref[mid + 1]) - pos[mid] * right_count

            if cost >= ans:
                break

        if cost < ans:
            ans = cost

    print(ans)


if __name__ == "__main__":
    solve()