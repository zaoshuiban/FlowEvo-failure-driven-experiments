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
    heap = []

    # Large enough to preserve the exact ordering of fractions
    # a / b with 1 <= b <= n.
    SCALE = (n + 1) * (n + 1) + 1

    for v in range(1, n + 1):
        if active[v]:
            cnt = 0
            for u in adj[v]:
                if active[u]:
                    cnt += 1

            current_degree[v] = cnt
            key = cnt * SCALE // degree[v]
            heapq.heappush(heap, (key, v, cnt))

    best_num = -1
    best_den = 1
    best_removed = 0

    removed_order = []
    removed_count = 0
    remaining = allowed_count

    while remaining > 0:
        while True:
            _, v, stored_degree = heapq.heappop(heap)
            if active[v] and stored_degree == current_degree[v]:
                break

        num = current_degree[v]
        den = degree[v]

        if num * best_den > best_num * den:
            best_num = num
            best_den = den
            best_removed = removed_count

        active[v] = False
        removed_order.append(v)
        remaining -= 1

        for u in adj[v]:
            if active[u]:
                current_degree[u] -= 1
                new_num = current_degree[u]
                new_key = new_num * SCALE // degree[u]
                heapq.heappush(heap, (new_key, u, new_num))

        removed_count += 1

    answer = removed_order[best_removed:]

    sys.stdout.write(str(len(answer)) + "\n")
    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    solve()