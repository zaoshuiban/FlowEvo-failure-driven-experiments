import sys

def main():
    input = sys.stdin.buffer.readline

    N, A, B, C = map(int, input().split())
    D = [list(map(int, input().split())) for _ in range(N)]

    INF = 10**30

    def dijkstra(start, multiplier, add_cost):
        dist = [INF] * N
        used = [False] * N
        dist[start] = 0

        for _ in range(N):
            v = -1
            best = INF

            for i in range(N):
                if not used[i] and dist[i] < best:
                    best = dist[i]
                    v = i

            if v == -1:
                break

            used[v] = True
            dv = dist[v]
            row = D[v]

            for to in range(N):
                if not used[to]:
                    nd = dv + multiplier * row[to] + add_cost
                    if nd < dist[to]:
                        dist[to] = nd

        return dist

    car_dist = dijkstra(0, A, 0)
    train_dist = dijkstra(N - 1, B, C)

    ans = min(car_dist[i] + train_dist[i] for i in range(N))
    print(ans)


if __name__ == "__main__":
    main()