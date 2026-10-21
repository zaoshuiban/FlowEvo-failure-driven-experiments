import sys

def main():
    n, h = map(int, sys.stdin.readline().split())

    # dp[limit][size] = number of binary trees with 'size' nodes
    # whose height is at most 'limit'
    dp = [[0] * (n + 1) for _ in range(n + 1)]

    dp[0][0] = 1

    for limit in range(1, n + 1):
        dp[limit][0] = 1
        for size in range(1, n + 1):
            count = 0
            for left in range(size):
                right = size - 1 - left
                count += dp[limit - 1][left] * dp[limit - 1][right]
            dp[limit][size] = count

    total = dp[n][n]
    less_than_h = dp[h - 1][n] if h > 1 else 0

    print(total - less_than_h)

if __name__ == "__main__":
    main()