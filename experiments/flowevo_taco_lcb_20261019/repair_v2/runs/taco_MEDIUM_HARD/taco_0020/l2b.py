import sys


def solve() -> None:
    data = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(data)

    answers = []
    INF = 10**9

    for _ in range(t):
        n = next(data)
        m = next(data)

        min_dp = [INF] * m
        max_dp = [-INF] * m

        for i in range(n):
            for j in range(m):
                value = next(data)

                if i == 0 and j == 0:
                    min_dp[j] = max_dp[j] = value
                elif i == 0:
                    min_dp[j] = min_dp[j - 1] + value
                    max_dp[j] = max_dp[j - 1] + value
                elif j == 0:
                    min_dp[j] = min_dp[j] + value
                    max_dp[j] = max_dp[j] + value
                else:
                    min_dp[j] = min(min_dp[j], min_dp[j - 1]) + value
                    max_dp[j] = max(max_dp[j], max_dp[j - 1]) + value

        if (n + m) % 2 == 0:
            answers.append("NO")
        elif min_dp[m - 1] <= 0 <= max_dp[m - 1]:
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()