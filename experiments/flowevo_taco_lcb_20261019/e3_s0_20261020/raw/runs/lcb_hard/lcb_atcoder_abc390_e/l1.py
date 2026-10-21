import sys
from bisect import bisect_left


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)
    X = next(it)

    NEG = -10**18
    dp = [[NEG] * (X + 1) for _ in range(3)]
    for v in range(3):
        dp[v][0] = 0

    total_a = 0

    for _ in range(N):
        v = next(it) - 1
        a = next(it)
        c = next(it)
        total_a += a

        arr = dp[v]
        for cost in range(X, c - 1, -1):
            candidate = arr[cost - c] + a
            if candidate > arr[cost]:
                arr[cost] = candidate

    for v in range(3):
        arr = dp[v]
        for cost in range(1, X + 1):
            if arr[cost - 1] > arr[cost]:
                arr[cost] = arr[cost - 1]

    low = 0
    high = total_a + 1

    while high - low > 1:
        mid = (low + high) // 2
        required_cost = 0
        ok = True

        for v in range(3):
            cost = bisect_left(dp[v], mid)
            required_cost += cost
            if required_cost > X:
                ok = False
                break

        if ok:
            low = mid
        else:
            high = mid

    print(low)


if __name__ == "__main__":
    main()