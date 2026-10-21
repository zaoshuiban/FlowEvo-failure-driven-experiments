import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    q = next(it)
    answers = []
    INF = 10**9

    for _ in range(q):
        n = next(it)
        t = [next(it) for _ in range(n)]
        t.sort()

        max_time = 2 * n + 5

        dp = [[INF] * (max_time + 1) for _ in range(n + 1)]

        for time in range(max_time + 1):
            dp[0][time] = 0

        for i in range(1, n + 1):
            for time in range(1, max_time + 1):
                take = dp[i - 1][time - 1] + abs(t[i - 1] - time)
                skip = dp[i][time - 1]
                dp[i][time] = min(take, skip)

        answers.append(str(dp[n][max_time]))

    print("\n".join(answers))


if __name__ == "__main__":
    solve()