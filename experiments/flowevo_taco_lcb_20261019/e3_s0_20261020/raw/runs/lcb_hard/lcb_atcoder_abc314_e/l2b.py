import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)
    M = next(it)

    wheels = []
    for _ in range(N):
        C = next(it)
        P = next(it)
        S = [next(it) for _ in range(P)]
        zero_count = S.count(0)
        positive = [s for s in S if s > 0]
        wheels.append((C, P, zero_count, positive))

    dp = [0.0] * (M + 1)

    for score in range(M - 1, -1, -1):
        best = float("inf")

        for C, P, zero_count, positive in wheels:
            pos_sum = 0.0
            for s in positive:
                nxt = score + s
                if nxt > M:
                    nxt = M
                pos_sum += dp[nxt]

            candidate = (C * P + pos_sum) / (P - zero_count)
            if candidate < best:
                best = candidate

        dp[score] = best

    print(f"{dp[0]:.15f}")


if __name__ == "__main__":
    main()