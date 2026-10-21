import sys


def main():
    input = sys.stdin.buffer.readline

    N, A, B, C = map(int, input().split())
    D = [list(map(int, input().split())) for _ in range(N)]

    INF = 10**30

    def dijkstra(start, multiplier, addition):
        dist = [INF] * N
        used = [False] * N
        dist[start] = 0

        for _ in range(N):
            u = -1
            best = INF

            for i in range(N):
                if not used[i] and dist[i] < best:
                    best = dist[i]
                    u = i

            if u == -1:
                break

            used[u] = True
            du = dist[u]
            row = D[u]

            for v in range(N):
                if not used[v]:
                    nd = du + row[v] * multiplier + addition
                    if nd < dist[v]:
                        dist[v] = nd

        return dist

    car_dist = dijkstra(0, A, 0)
    train_dist = dijkstra(N - 1, B, C)

    answer = min(car_dist[i] + train_dist[i] for i in range(N))
    print(answer)


if __name__ == "__main__":
    main()