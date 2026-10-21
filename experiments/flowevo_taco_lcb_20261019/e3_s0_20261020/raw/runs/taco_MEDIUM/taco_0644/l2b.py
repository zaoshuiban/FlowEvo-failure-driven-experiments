import sys
import heapq


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    graph = [[] for _ in range(n + 1)]

    idx = 2
    for _ in range(m):
        u, v = data[idx], data[idx + 1]
        idx += 2
        graph[u].append(v)
        graph[v].append(u)

    visited = [False] * (n + 1)
    heap = [1]
    answer = []

    while heap:
        u = heapq.heappop(heap)

        if visited[u]:
            continue

        visited[u] = True
        answer.append(u)

        for v in graph[u]:
            if not visited[v]:
                heapq.heappush(heap, v)

    sys.stdout.write(" ".join(map(str, answer)))


if __name__ == "__main__":
    main()