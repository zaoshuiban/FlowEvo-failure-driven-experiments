import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []
    INF = 10**15

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        dist = [[INF] * n for _ in range(n)]
        for i in range(n):
            dist[i][i] = 0

        for _ in range(m):
            x = data[idx] - 1
            y = data[idx + 1] - 1
            c = data[idx + 2]
            idx += 3

            if c < dist[x][y]:
                dist[x][y] = c
                dist[y][x] = c

        s = data[idx] - 1
        a = data[idx + 1] - 1
        h = data[idx + 2] - 1
        idx += 3

        # Floyd-Warshall
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

        ans = 0

        for v in range(n):
            if v != s and v != a and v != h:
                time_needed = dist[s][v] + 2 * dist[a][v] + dist[h][v]
                if time_needed > ans:
                    ans = time_needed

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()