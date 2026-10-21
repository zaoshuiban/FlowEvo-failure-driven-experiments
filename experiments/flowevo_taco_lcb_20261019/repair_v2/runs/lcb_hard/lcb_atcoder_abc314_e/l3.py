import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    N, M = data[0], data[1]
    idx = 2

    wheels = []
    for _ in range(N):
        C = data[idx]
        P = data[idx + 1]
        idx += 2

        S = data[idx:idx + P]
        idx += P

        zero_count = S.count(0)
        positive = [s for s in S if s > 0]
        wheels.append((C, P, zero_count, positive))

    dp = [0.0] * (M + 1)

    for score in range(M - 1, -1, -1):
        best = float("inf")

        for C, P, zero_count, positive in wheels:
            numerator = C * P

            for s in positive:
                nxt = score + s
                if nxt > M:
                    nxt = M
                numerator += dp[nxt]

            candidate = numerator / (P - zero_count)
            if candidate < best:
                best = candidate

        dp[score] = best

    print(f"{dp[0]:.15f}")


if __name__ == "__main__":
    main()