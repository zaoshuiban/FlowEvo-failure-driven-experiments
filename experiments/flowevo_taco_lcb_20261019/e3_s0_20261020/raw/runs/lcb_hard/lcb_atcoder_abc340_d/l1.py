import sys
import heapq


def main():
    input = sys.stdin.buffer.readline

    N = int(input())

    A = [0] * (N + 1)
    B = [0] * (N + 1)
    X = [0] * (N + 1)

    for i in range(1, N):
        a, b, x = map(int, input().split())
        A[i] = a
        B[i] = b
        X[i] = x

    INF = 10**30
    dist = [INF] * (N + 1)
    dist[1] = 0

    pq = [(0, 1)]

    while pq:
        d, v = heapq.heappop(pq)

        if d != dist[v]:
            continue

        if v == N:
            print(d)
            return

        if v < N:
            nd = d + A[v]
            if nd < dist[v + 1]:
                dist[v + 1] = nd
                heapq.heappush(pq, (nd, v + 1))

            to = X[v]
            nd = d + B[v]
            if nd < dist[to]:
                dist[to] = nd
                heapq.heappush(pq, (nd, to))

    print(dist[N])


if __name__ == "__main__":
    main()