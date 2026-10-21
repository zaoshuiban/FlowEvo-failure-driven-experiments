import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    p = float(data[1])
    t = int(data[2])

    q = 1.0 - p
    dp = [0.0] * (n + 1)
    dp[0] = 1.0

    for second in range(t):
        ndp = [0.0] * (n + 1)
        limit = min(second, n)

        for j in range(limit + 1):
            prob = dp[j]
            if prob == 0.0:
                continue

            if j == n:
                ndp[n] += prob
            else:
                ndp[j] += prob * q
                ndp[j + 1] += prob * p

        dp = ndp

    answer = sum(i * dp[i] for i in range(1, n + 1))
    print(f"{answer:.10f}")


if __name__ == "__main__":
    main()