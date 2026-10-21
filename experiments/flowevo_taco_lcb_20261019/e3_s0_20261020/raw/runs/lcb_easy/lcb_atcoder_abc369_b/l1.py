import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    N = int(data[0])
    MAX_KEY = 100
    INF = 10**18

    # dp[l][r]: minimum fatigue after processed presses,
    # with left hand at l and right hand at r.
    dp = [[0] * (MAX_KEY + 1) for _ in range(MAX_KEY + 1)]

    idx = 1
    for _ in range(N):
        a = int(data[idx])
        s = data[idx + 1]
        idx += 2

        ndp = [[INF] * (MAX_KEY + 1) for _ in range(MAX_KEY + 1)]

        if s == 'L':
            for r in range(1, MAX_KEY + 1):
                best = INF
                for l in range(1, MAX_KEY + 1):
                    cost = dp[l][r] + abs(a - l)
                    if cost < best:
                        best = cost
                ndp[a][r] = best
        else:
            for l in range(1, MAX_KEY + 1):
                best = INF
                for r in range(1, MAX_KEY + 1):
                    cost = dp[l][r] + abs(a - r)
                    if cost < best:
                        best = cost
                ndp[l][a] = best

        dp = ndp

    answer = INF
    for l in range(1, MAX_KEY + 1):
        for r in range(1, MAX_KEY + 1):
            answer = min(answer, dp[l][r])

    print(answer)


if __name__ == "__main__":
    main()