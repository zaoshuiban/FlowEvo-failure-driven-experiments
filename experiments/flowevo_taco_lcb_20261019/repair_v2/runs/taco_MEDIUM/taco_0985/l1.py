import sys

def solve() -> None:
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    strings = data[2:2 + n]

    INF = 10**9
    cost = [[INF] * 3 for _ in range(n)]

    for i, s in enumerate(strings):
        for pos, ch in enumerate(s):
            if '0' <= ch <= '9':
                typ = 0
            elif 'a' <= ch <= 'z':
                typ = 1
            else:
                typ = 2

            moves = min(pos, m - pos)
            if moves < cost[i][typ]:
                cost[i][typ] = moves

    ans = INF

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            for k in range(n):
                if k == i or k == j:
                    continue

                cur = cost[i][0] + cost[j][1] + cost[k][2]
                if cur < ans:
                    ans = cur

    print(ans)


if __name__ == "__main__":
    solve()