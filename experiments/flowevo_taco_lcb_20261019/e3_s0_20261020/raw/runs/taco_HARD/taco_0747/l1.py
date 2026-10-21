import sys

def solve() -> None:
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    h = int(data[1])

    # dp[k][H] = number of BSTs with k nodes and height at most H
    dp = [[0] * (n + 1) for _ in range(n + 1)]

    for H in range(n + 1):
        dp[0][H] = 1

    for H in range(1, n + 1):
        for nodes in range(1, n + 1):
            total = 0
            for left in range(nodes):
                right = nodes - 1 - left
                total += dp[left][H - 1] * dp[right][H - 1]
            dp[nodes][H] = total

    total_trees = dp[n][n]
    lower_than_h = dp[n][h - 1] if h - 1 >= 0 else 0

    print(total_trees - lower_than_h)


if __name__ == "__main__":
    solve()