import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    N, M = data[0], data[1]
    idx = 2

    wheels = []
    for _ in range(N):
        cost = data[idx]
        p = data[idx + 1]
        idx += 2

        outcomes = data[idx:idx + p]
        idx += p

        positive = [x for x in outcomes if x > 0]
        wheels.append((cost, p, positive))

    dp = [0.0] * (M + 1)
    INF = float("inf")

    for score in range(M - 1, -1, -1):
        best = INF

        for cost, p, positive in wheels:
            den = len(positive)
            if den == 0:
                continue

            total = cost * p

            for gain in positive:
                nxt = score + gain
                if nxt > M:
                    nxt = M
                total += dp[nxt]

            candidate = total / den
            if candidate < best:
                best = candidate

        dp[score] = best

    print("{:.15f}".format(dp[0]))


if __name__ == "__main__":
    main()