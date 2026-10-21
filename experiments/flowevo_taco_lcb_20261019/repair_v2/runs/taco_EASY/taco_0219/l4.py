import sys
import heapq


def dijkstra(start, n, graph):
    INF = 10**18
    dist = [INF] * (n + 1)
    dist[start] = 0
    pq = [(0, start)]

    while pq:
        cur_dist, u = heapq.heappop(pq)

        if cur_dist != dist[u]:
            continue

        for v, w in graph[u]:
            nxt = cur_dist + w
            if nxt < dist[v]:
                dist[v] = nxt
                heapq.heappush(pq, (nxt, v))

    return dist


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        graph = [[] for _ in range(n + 1)]

        for _ in range(m):
            x = data[idx]
            y = data[idx + 1]
            c = data[idx + 2]
            idx += 3

            graph[x].append((y, c))
            graph[y].append((x, c))

        s = data[idx]
        a = data[idx + 1]
        h = data[idx + 2]
        idx += 3

        dist_s = dijkstra(s, n, graph)
        dist_a = dijkstra(a, n, graph)
        dist_h = dijkstra(h, n, graph)

        special = {s, a, h}
        answer = 0

        for building in range(1, n + 1):
            if building not in special:
                time_needed = (
                    dist_s[building]
                    + 2 * dist_a[building]
                    + dist_h[building]
                )
                answer = max(answer, time_needed)

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()