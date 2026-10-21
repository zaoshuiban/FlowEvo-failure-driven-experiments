import sys
import heapq


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1
    m = data[idx]
    idx += 1

    x = data[idx] - 1
    idx += 1
    y = data[idx] - 1
    idx += 1

    graph = [[] for _ in range(n)]

    for _ in range(m):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        w = data[idx + 2]
        idx += 3
        graph[u].append((v, w))
        graph[v].append((u, w))

    taxi_dist = [0] * n
    taxi_cost = [0] * n

    for i in range(n):
        taxi_dist[i] = data[idx]
        taxi_cost[i] = data[idx + 1]
        idx += 2

    if x == y:
        print(0)
        return

    INF = 10**30
    min_cost = [INF] * n
    min_cost[x] = 0

    pq = [(0, x)]
    heappop = heapq.heappop
    heappush = heapq.heappush

    while pq:
        current_cost, u = heappop(pq)

        if current_cost != min_cost[u]:
            continue

        if u == y:
            print(current_cost)
            return

        limit = taxi_dist[u]

        road_dist = [INF] * n
        road_dist[u] = 0
        road_pq = [(0, u)]

        reachable = []

        while road_pq:
            dist, v = heappop(road_pq)

            if dist != road_dist[v]:
                continue

            reachable.append(v)

            for to, weight in graph[v]:
                new_dist = dist + weight
                if new_dist <= limit and new_dist < road_dist[to]:
                    road_dist[to] = new_dist
                    heappush(road_pq, (new_dist, to))

        next_cost = current_cost + taxi_cost[u]

        for v in reachable:
            if v == u:
                continue

            if next_cost < min_cost[v]:
                min_cost[v] = next_cost
                heappush(pq, (next_cost, v))

    print(-1)


if __name__ == "__main__":
    solve()