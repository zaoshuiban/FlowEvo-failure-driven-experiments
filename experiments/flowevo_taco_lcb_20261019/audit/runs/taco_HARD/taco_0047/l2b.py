import sys
import heapq


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m, k = data[0], data[1], data[2]
    idx = 3

    fortress = [False] * (n + 1)
    for _ in range(k):
        fortress[data[idx]] = True
        idx += 1

    adj = [[] for _ in range(n + 1)]
    degree = [0] * (n + 1)

    for _ in range(m):
        a = data[idx]
        b = data[idx + 1]
        idx += 2
        adj[a].append(b)
        adj[b].append(a)
        degree[a] += 1
        degree[b] += 1

    active = [False] * (n + 1)
    allowed_count = 0

    for v in range(1, n + 1):
        if not fortress[v]:
            active[v] = True
            allowed_count += 1

    current_degree = [0] * (n + 1)

    for v in range(1, n + 1):
        if active[v]:
            cnt = 0
            for u in adj[v]:
                if active[u]:
                    cnt += 1
            current_degree[v] = cnt

    heap = []
    for v in range(1, n + 1):
        if active[v]:
            heapq.heappush(
                heap,
                (current_degree[v] / degree[v], v, current_degree[v])
            )

    best_ratio = -1.0
    best_removed = 0

    removed_order = []
    removed_count = 0
    remaining = allowed_count

    while remaining > 0:
        while True:
            ratio, v, stored_degree = heapq.heappop(heap)
            if active[v] and stored_degree == current_degree[v]:
                break

        if ratio > best_ratio:
            best_ratio = ratio
            best_removed = removed_count

        active[v] = False
        removed_order.append(v)
        remaining -= 1

        for u in adj[v]:
            if active[u]:
                current_degree[u] -= 1
                heapq.heappush(
                    heap,
                    (current_degree[u] / degree[u], u, current_degree[u])
                )

        removed_count += 1

    answer = removed_order[best_removed:]

    sys.stdout.write(str(len(answer)) + "\n")
    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    solve()