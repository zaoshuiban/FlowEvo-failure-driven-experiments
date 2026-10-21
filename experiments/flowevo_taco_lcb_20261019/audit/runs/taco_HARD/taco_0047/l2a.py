import sys
import heapq


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)
    k = next(it)

    forbidden = [False] * (n + 1)
    for _ in range(k):
        forbidden[next(it)] = True

    adj = [[] for _ in range(n + 1)]
    for _ in range(m):
        a = next(it)
        b = next(it)
        adj[a].append(b)
        adj[b].append(a)

    # `removed[v]` is True if v is a fortress or has already been removed
    # from the current candidate set.
    removed = forbidden[:]

    degree = [0] * (n + 1)
    allowed = []

    for v in range(1, n + 1):
        degree[v] = len(adj[v])
        if not forbidden[v]:
            allowed.append(v)

    inside = [0] * (n + 1)
    heap = []
    heappush = heapq.heappush
    heappop = heapq.heappop

    for v in allowed:
        cnt = 0
        for u in adj[v]:
            if not removed[u]:
                cnt += 1
        inside[v] = cnt
        heappush(heap, (cnt / degree[v], v, cnt))

    pos = [-1] * (n + 1)

    best_num = 0
    best_den = 1
    best_removed = 0

    removed_count = 0

    while heap:
        while heap:
            _, v, cnt = heap[0]
            if removed[v] or cnt != inside[v]:
                heappop(heap)
            else:
                break

        if not heap:
            break

        _, v, cnt = heap[0]
        den = degree[v]

        # Compare cnt / den with best_num / best_den.
        if cnt * best_den > best_num * den:
            best_num = cnt
            best_den = den
            best_removed = removed_count

        heappop(heap)
        removed[v] = True
        pos[v] = removed_count
        removed_count += 1

        for u in adj[v]:
            if not removed[u]:
                inside[u] -= 1
                heappush(heap, (inside[u] / degree[u], u, inside[u]))

    answer = [str(v) for v in allowed if pos[v] >= best_removed]

    sys.stdout.write(str(len(answer)) + "\n")
    sys.stdout.write(" ".join(answer))


if __name__ == "__main__":
    main()