import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    ones = [i + 1 for i, x in enumerate(a) if x == 1]
    zeros = [i + 1 for i, x in enumerate(a) if x == 0]

    m = len(ones)
    if m == 0:
        print(0)
        return

    INF = 10**18
    dp = [INF] * (m + 1)
    dp[0] = 0

    used_zeros = 0

    for z in zeros:
        upper = min(m, used_zeros + 1)

        for j in range(upper, 0, -1):
            cost = dp[j - 1] + abs(ones[j - 1] - z)
            if cost < dp[j]:
                dp[j] = cost

        used_zeros += 1

    print(dp[m])


if __name__ == "__main__":
    solve()