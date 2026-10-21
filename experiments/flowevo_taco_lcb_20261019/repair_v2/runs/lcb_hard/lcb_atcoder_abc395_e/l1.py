import sys
import heapq


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    N = next(it)
    M = next(it)
    X = next(it)

    graph = [[] for _ in range(N + 1)]
    reverse_graph = [[] for _ in range(N + 1)]

    for _ in range(M):
        u = next(it)
        v = next(it)
        graph[u].append(v)
        reverse_graph[v].append(u)

    INF = 10**30

    # dist0[v]: minimum cost at vertex v when edges are in the original direction
    # dist1[v]: minimum cost at vertex v when all edges are reversed
    dist0 = [INF] * (N + 1)
    dist1 = [INF] * (N + 1)

    dist0[1] = 0
    heap = [(0, 1, 0)]  # (cost, vertex, orientation)

    heapq.heapify(heap)

    while heap:
        cost, v, state = heapq.heappop(heap)

        if state == 0:
            if cost != dist0[v]:
                continue

            if v == N:
                print(cost)
                return

            # Reverse all edges
            next_cost = cost + X
            if next_cost < dist1[v]:
                dist1[v] = next_cost
                heapq.heappush(heap, (next_cost, v, 1))

            # Move along an original directed edge
            next_cost = cost + 1
            for to in graph[v]:
                if next_cost < dist0[to]:
                    dist0[to] = next_cost
                    heapq.heappush(heap, (next_cost, to, 0))

        else:
            if cost != dist1[v]:
                continue

            if v == N:
                print(cost)
                return

            # Reverse all edges
            next_cost = cost + X
            if next_cost < dist0[v]:
                dist0[v] = next_cost
                heapq.heappush(heap, (next_cost, v, 0))

            # Move along a reversed original edge
            next_cost = cost + 1
            for to in reverse_graph[v]:
                if next_cost < dist1[to]:
                    dist1[to] = next_cost
                    heapq.heappush(heap, (next_cost, to, 1))


if __name__ == "__main__":
    main()