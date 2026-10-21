import sys

def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    p = float(data[1])
    t = int(data[2])

    q = 1.0 - p

    # dp[i] = probability that exactly i people are standing on the escalator.
    # dp[n] is absorbing: once all n people have entered, the count remains n.
    dp = [0.0] * (n + 1)
    dp[0] = 1.0

    for _ in range(t):
        ndp = [0.0] * (n + 1)

        for i in range(n):
            prob = dp[i]
            if prob == 0.0:
                continue

            ndp[i] += prob * q
            ndp[i + 1] += prob * p

        # If all n people have already entered, they remain on the escalator.
        ndp[n] += dp[n]

        dp = ndp

    answer = sum(i * dp[i] for i in range(n + 1))
    print(f"{answer:.15f}")


if __name__ == "__main__":
    main()