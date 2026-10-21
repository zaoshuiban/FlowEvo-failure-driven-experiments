import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    q = data[0]
    idx = 1
    answers = []
    INF = 10**9

    for _ in range(q):
        n = data[idx]
        idx += 1
        times = data[idx:idx + n]
        idx += n

        times.sort()
        limit = 2 * n

        dp = [[INF] * (limit + 1) for _ in range(n + 1)]

        for j in range(limit + 1):
            dp[0][j] = 0

        for i in range(1, n + 1):
            for j in range(1, limit + 1):
                dp[i][j] = min(
                    dp[i][j - 1],
                    dp[i - 1][j - 1] + abs(times[i - 1] - j)
                )

        answers.append(str(dp[n][limit]))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()