import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    answers = []
    INF = 10**15

    for _ in range(t):
        n = next(it)
        m = next(it)

        dist = [[INF] * n for _ in range(n)]
        for i in range(n):
            dist[i][i] = 0

        for _ in range(m):
            x = next(it) - 1
            y = next(it) - 1
            c = next(it)
            if c < dist[x][y]:
                dist[x][y] = c
                dist[y][x] = c

        s = next(it) - 1
        a = next(it) - 1
        h = next(it) - 1

        for k in range(n):
            dk = dist[k]
            for i in range(n):
                dik = dist[i][k]
                if dik == INF:
                    continue
                di = dist[i]
                for j in range(n):
                    nd = dik + dk[j]
                    if nd < di[j]:
                        di[j] = nd

        excluded = {s, a, h}
        ans = 0

        for i in range(n):
            if i not in excluded:
                time_needed = dist[s][i] + 2 * dist[a][i] + dist[h][i]
                if time_needed > ans:
                    ans = time_needed

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()