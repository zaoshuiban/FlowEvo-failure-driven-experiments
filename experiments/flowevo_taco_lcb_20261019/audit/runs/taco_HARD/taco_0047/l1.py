import sys
import heapq


class Node:
    __slots__ = ("c", "d", "v")

    def __init__(self, c, d, v):
        self.c = c
        self.d = d
        self.v = v

    def __lt__(self, other):
        left = self.c * other.d
        right = other.c * self.d
        if left != right:
            return left < right
        return self.v < other.v


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    n = int(next(it))
    m = int(next(it))
    k = int(next(it))

    forbidden = bytearray(n + 1)
    for _ in range(k):
        forbidden[int(next(it))] = 1

    adj = [[] for _ in range(n + 1)]
    for _ in range(m):
        a = int(next(it))
        b = int(next(it))
        adj[a].append(b)
        adj[b].append(a)

    degree = [0] * (n + 1)
    for v in range(1, n + 1):
        degree[v] = len(adj[v])

    internal = [0] * (n + 1)
    heap = []

    for v in range(1, n + 1):
        if not forbidden[v]:
            cnt = 0
            for u in adj[v]:
                if not forbidden[u]:
                    cnt += 1
            internal[v] = cnt
            heap.append(Node(cnt, degree[v], v))

    heapq.heapify(heap)

    removed = bytearray(n + 1)
    order = [0] * (n + 1)

    removed_count = 0

    best_c = -1
    best_d = 1
    best_time = 0

    while heap:
        while heap:
            node = heap[0]
            v = node.v
            if not removed[v] and internal[v] == node.c:
                break
            heapq.heappop(heap)

        if not heap:
            break

        node = heap[0]
        v = node.v
        cur_c = node.c
        cur_d = degree[v]

        if cur_c * best_d > best_c * cur_d:
            best_c = cur_c
            best_d = cur_d
            best_time = removed_count

        heapq.heappop(heap)
        removed[v] = 1
        order[v] = removed_count
        removed_count += 1

        for u in adj[v]:
            if not forbidden[u] and not removed[u]:
                internal[u] -= 1
                heapq.heappush(heap, Node(internal[u], degree[u], u))

    answer = []
    for v in range(1, n + 1):
        if not forbidden[v] and order[v] >= best_time:
            answer.append(str(v))

    sys.stdout.write(str(len(answer)) + "\n")
    sys.stdout.write(" ".join(answer) + "\n")


if __name__ == "__main__":
    solve()