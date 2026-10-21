import sys

def main():
    input = sys.stdin.readline
    N = int(input())
    S = input().strip()

    moves = "RPS"
    NEG = -10**9

    def result(t, a):
        # 1 if Takahashi wins, 0 if draw, -1 if loses
        if t == a:
            return 0
        if (t == "R" and a == "S") or \
           (t == "P" and a == "R") or \
           (t == "S" and a == "P"):
            return 1
        return -1

    dp = [NEG] * 3

    for i, t in enumerate(moves):
        res = result(t, S[0])
        if res >= 0:
            dp[i] = res

    for i in range(1, N):
        ndp = [NEG] * 3
        a = S[i]

        for j, t in enumerate(moves):
            res = result(t, a)
            if res < 0:
                continue

            best = NEG
            for k in range(3):
                if k != j:
                    best = max(best, dp[k])

            if best != NEG:
                ndp[j] = best + res

        dp = ndp

    print(max(dp))


if __name__ == "__main__":
    main()