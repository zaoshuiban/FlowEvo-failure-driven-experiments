import sys
import heapq

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N = data[0]
    A = [0] * (N - 1)
    B = [0] * (N - 1)
    X = [0] * (N - 1)

    idx = 1
    for i in range(N - 1):
        A[i], B[i], X[i] = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

    INF = 10**30
    dist = [INF] * N
    dist[0] = 0
    pq = [(0, 0)]

    while pq:
        d, v = heapq.heappop(pq)
        if d != dist[v]:
            continue
        if v == N - 1:
            break

        nd = d + A[v]
        nv = v + 1
        if nd < dist[nv]:
            dist[nv] = nd
            heapq.heappush(pq, (nd, nv))

        nd = d + B[v]
        nv = X[v] - 1
        if nd < dist[nv]:
            dist[nv] = nd
            heapq.heappush(pq, (nd, nv))

    print(dist[N - 1])

if __name__ == "__main__":
    main()