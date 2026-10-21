import sys

def main():
    input = sys.stdin.readline

    n, m = map(int, input().split())

    INF = 10**9
    costs = []

    for _ in range(n):
        s = input().strip()
        best = [INF, INF, INF]

        for i, ch in enumerate(s):
            dist = min(i, m - i)

            if '0' <= ch <= '9':
                t = 0
            elif 'a' <= ch <= 'z':
                t = 1
            else:
                t = 2

            best[t] = min(best[t], dist)

        costs.append(best)

    dp = [INF] * 8
    dp[0] = 0

    for cost in costs:
        ndp = dp[:]

        for mask in range(8):
            if dp[mask] == INF:
                continue

            for t in range(3):
                if cost[t] == INF:
                    continue

                new_mask = mask | (1 << t)
                ndp[new_mask] = min(ndp[new_mask], dp[mask] + cost[t])

        dp = ndp

    print(dp[7])


if __name__ == "__main__":
    main()