import sys

def main() -> None:
    data = sys.stdin.read().split()
    n = int(data[0])
    p = float(data[1])
    t = int(data[2])

    dp = [0.0] * (n + 1)
    dp[0] = 1.0

    q = 1.0 - p

    for _ in range(t):
        ndp = [0.0] * (n + 1)

        for i in range(n):
            if dp[i] == 0.0:
                continue
            ndp[i] += dp[i] * q
            ndp[i + 1] += dp[i] * p

        ndp[n] += dp[n]
        dp = ndp

    expected = sum(i * dp[i] for i in range(n + 1))
    print(f"{expected:.10f}")

if __name__ == "__main__":
    main()