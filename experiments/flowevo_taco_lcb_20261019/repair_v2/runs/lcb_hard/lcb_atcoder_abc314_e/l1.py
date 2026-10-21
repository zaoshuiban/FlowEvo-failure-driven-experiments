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
        outcomes = [next(it) for _ in range(P)]
        positives = [s for s in outcomes if s > 0]
        roulettes.append((C, P, positives))

    dp = [0.0] * (M + 1)

    for need in range(1, M + 1):
        best = float("inf")

        for C, P, positives in roulettes:
            numerator = C * P
            for s in positives:
                if s >= need:
                    continue
                numerator += dp[need - s]

            denominator = len(positives)
            candidate = numerator / denominator
            if candidate < best:
                best = candidate

        dp[need] = best

    print(f"{dp[M]:.15f}")

if __name__ == "__main__":
    main()