import sys
import heapq

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    n = int(next(it))
    m = int(next(it))

    adj = [[] for _ in range(n + 1)]

    for _ in range(m):
        u = int(next(it))
        v = int(next(it))
        adj[u].append(v)
        adj[v].append(u)

    visited = bytearray(n + 1)
    visited[1] = 1

    ans = [1]
    heap = []

    for v in adj[1]:
        if not visited[v]:
            heapq.heappush(heap, v)

    while heap:
        u = heapq.heappop(heap)

        if visited[u]:
            continue

        visited[u] = 1
        ans.append(u)

        for v in adj[u]:
            if not visited[v]:
                heapq.heappush(heap, v)

    print(*ans)

if __name__ == "__main__":
    solve()