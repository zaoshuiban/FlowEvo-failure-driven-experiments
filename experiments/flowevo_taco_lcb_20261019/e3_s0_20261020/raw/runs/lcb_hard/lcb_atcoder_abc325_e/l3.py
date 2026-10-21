import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, A, B, C = data[:4]
    offset = 4
    INF = 10**30

    def dijkstra(start, multiplier, addition):
        dist = [INF] * N
        used = [False] * N
        dist[start] = 0

        for _ in range(N):
            best = INF
            u = -1

            for i in range(N):
                if not used[i] and dist[i] < best:
                    best = dist[i]
                    u = i

            if u == -1:
                break

            used[u] = True
            row_start = offset + u * N

            for v in range(N):
                if not used[v]:
                    nd = best + data[row_start + v] * multiplier + addition
                    if nd < dist[v]:
                        dist[v] = nd

        return dist

    car_dist = dijkstra(0, A, 0)
    train_dist = dijkstra(N - 1, B, C)

    answer = min(car_dist[i] + train_dist[i] for i in range(N))
    print(answer)


if __name__ == "__main__":
    main()