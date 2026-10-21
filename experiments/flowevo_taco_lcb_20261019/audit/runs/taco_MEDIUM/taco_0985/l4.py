import sys


def main():
    input = sys.stdin.readline

    n, m = map(int, input().split())
    INF = 10**9

    # costs[i][0] = moves needed to make row i a digit
    # costs[i][1] = moves needed to make row i a lowercase letter
    # costs[i][2] = moves needed to make row i a special character (#, *, &)
    costs = [[INF, INF, INF] for _ in range(n)]

    for i in range(n):
        s = input().strip()

        for pos, ch in enumerate(s):
            if '0' <= ch <= '9':
                typ = 0
            elif 'a' <= ch <= 'z':
                typ = 1
            elif ch in '#*&':
                typ = 2
            else:
                continue

            moves = min(pos, m - pos)
            if moves < costs[i][typ]:
                costs[i][typ] = moves

    # dp[mask] = minimum moves after processing some rows,
    # where mask shows which required character types are already present.
    dp = [INF] * 8
    dp[0] = 0

    for i in range(n):
        ndp = dp[:]  # Option: leave row i unchanged for password requirements

        for mask in range(8):
            if dp[mask] == INF:
                continue

            for typ in range(3):
                if costs[i][typ] == INF:
                    continue

                new_mask = mask | (1 << typ)
                new_cost = dp[mask] + costs[i][typ]

                if new_cost < ndp[new_mask]:
                    ndp[new_mask] = new_cost

        dp = ndp

    print(dp[7])


if __name__ == "__main__":
    main()