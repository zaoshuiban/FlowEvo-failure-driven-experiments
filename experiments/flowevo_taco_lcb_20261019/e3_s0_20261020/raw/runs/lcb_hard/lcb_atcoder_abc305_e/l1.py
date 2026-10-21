import sys
import heapq


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)
    M = next(it)
    K = next(it)

    graph = [[] for _ in range(N + 1)]

    for _ in range(M):
        a = next(it)
        b = next(it)
        graph[a].append(b)
        graph[b].append(a)

    best = [-1] * (N + 1)
    heap = []

    for _ in range(K):
        p = next(it)
        h = next(it)
        if h > best[p]:
            best[p] = h
            heap.append((-h, p))

    heapq.heapify(heap)

    while heap:
        neg_rem, u = heapq.heappop(heap)
        rem = -neg_rem

        if rem != best[u]:
            continue

        next_rem = rem - 1
        if next_rem < 0:
            continue

        for v in graph[u]:
            if next_rem > best[v]:
                best[v] = next_rem
                heapq.heappush(heap, (-next_rem, v))

    ans = [str(i) for i in range(1, N + 1) if best[i] >= 0]

    output = [str(len(ans)), " ".join(ans)]
    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()