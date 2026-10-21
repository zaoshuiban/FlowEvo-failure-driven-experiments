import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    p = float(data[1])
    t = int(data[2])

    n = min(n, t)
    q = 1.0 - p

    dp = [0.0] * (n + 1)
    dp[0] = 1.0

    for _ in range(t):
        old_last_before_n = dp[n - 1]

        for k in range(n - 1, 0, -1):
            dp[k] = dp[k] * q + dp[k - 1] * p

        dp[0] *= q
        dp[n] += old_last_before_n * p

    ans = sum(i * dp[i] for i in range(1, n + 1))
    print(f"{ans:.10f}")

if __name__ == "__main__":
    main()