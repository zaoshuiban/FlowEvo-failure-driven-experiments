import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    left = [[0] * (m + 1) for _ in range(n)]
    right = [[0] * (m + 1) for _ in range(n)]

    for row in range(n):
        k = next(it)
        for _ in range(k):
            l = next(it)
            r = next(it)
            for col in range(l, r + 1):
                left[row][col] = l
                right[row][col] = r

    dp = [[0] * (m + 2) for _ in range(m + 2)]

    for length in range(1, m + 1):
        for l in range(1, m - length + 2):
            r = l + length - 1
            best = 0

            for mid in range(l, r + 1):
                count = 0

                for row in range(n):
                    if left[row][mid] >= l and right[row][mid] <= r:
                        count += 1

                value = dp[l][mid - 1] + dp[mid + 1][r] + count * count
                if value > best:
                    best = value

            dp[l][r] = best

    print(dp[1][m])


if __name__ == "__main__":
    solve()