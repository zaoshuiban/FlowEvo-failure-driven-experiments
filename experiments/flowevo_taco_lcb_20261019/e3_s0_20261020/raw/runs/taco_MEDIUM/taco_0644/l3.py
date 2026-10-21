import sys
import heapq


def solve() -> None:
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
    visited[1] = True

    heap = [1]
    answer = []

    while heap:
        u = heapq.heappop(heap)
        answer.append(u)

        for v in graph[u]:
            if not visited[v]:
                visited[v] = True
                heapq.heappush(heap, v)

    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    solve()