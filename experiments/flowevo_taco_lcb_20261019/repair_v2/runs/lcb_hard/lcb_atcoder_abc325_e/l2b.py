import sys


def dijkstra(dist_matrix, start, multiplier, addition):
    n = len(dist_matrix)
    INF = 10**30

    dist = [INF] * n
    used = [False] * n
    dist[start] = 0

    for _ in range(n):
        best = INF
        u = -1

        for i in range(n):
            if not used[i] and dist[i] < best:
                best = dist[i]
                u = i

        if u == -1:
            break

        used[u] = True
        row = dist_matrix[u]

        for v in range(n):
            if not used[v]:
                nd = best + row[v] * multiplier + addition
                if nd < dist[v]:
                    dist[v] = nd

    return dist


def main():
    input = sys.stdin.buffer.readline

    N, A, B, C = map(int, input().split())

    D = []
    for _ in range(N):
        D.append(list(map(int, input().split())))

    car_dist = dijkstra(D, 0, A, 0)
    train_dist = dijkstra(D, N - 1, B, C)

    answer = min(car_dist[i] + train_dist[i] for i in range(N))
    print(answer)


if __name__ == "__main__":
    main()