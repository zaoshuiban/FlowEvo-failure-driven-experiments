import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)
    M = next(it)

    roulettes = []
    for _ in range(N):
        C = next(it)
        P = next(it)
        S = [next(it) for _ in range(P)]
        roulettes.append((C, P, S))

    # dp[r] = minimum expected additional cost to get at least r more points
    dp = [0.0] * (M + 1)

    for r in range(1, M + 1):
        best = float("inf")

        for C, P, S in roulettes:
            total = 0.0
            zero_count = 0

            for s in S:
                if s == 0:
                    zero_count += 1
                else:
                    remaining = r - s
                    if remaining > 0:
                        total += dp[remaining]
                    # If remaining <= 0, dp[0] = 0

            denominator = P - zero_count
            expected_cost = (C * P + total) / denominator
            if expected_cost < best:
                best = expected_cost

        dp[r] = best

    print(f"{dp[M]:.15f}")


if __name__ == "__main__":
    main()