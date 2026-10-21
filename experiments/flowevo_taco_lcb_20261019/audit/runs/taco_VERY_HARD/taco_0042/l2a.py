import sys
from collections import deque


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    output = []

    for _ in range(t):
        n = next(it)
        m = next(it)
        k = next(it)

        adj = [[] for _ in range(n)]
        first_edge = None

        clique_possible = (k > 2 and k * (k - 1) // 2 <= m)
        edge_set = set() if clique_possible else None

        for _ in range(m):
            u = next(it) - 1
            v = next(it) - 1

            adj[u].append(v)
            adj[v].append(u)

            if first_edge is None:
                first_edge = (u, v)

            if clique_possible:
                if u < v:
                    edge_set.add(u * n + v)
                else:
                    edge_set.add(v * n + u)

        if k == 1:
            output.append("2")
            output.append("1")
            continue

        if k == 2:
            if m > 0:
                u, v = first_edge
                output.append("2")
                output.append(f"{u + 1} {v + 1}")
            else:
                output.append("-1")
            continue

        if clique_possible:
            for lst in adj:
                lst.sort()

        degree = [len(x) for x in adj]
        removed = bytearray(n)
        active_count = n

        queue = deque(i for i in range(n) if degree[i] < k)

        found_clique = None
        failed_neighborhoods = set() if clique_possible else None

        while queue:
            v = queue.popleft()

            if removed[v]:
                continue

            if degree[v] >= k:
                continue

            if clique_possible and degree[v] == k - 1:
                neighbours = []
                for u in adj[v]:
                    if not removed[u]:
                        neighbours.append(u)

                if len(neighbours) == k - 1:
                    key = tuple(neighbours)

                    if key not in failed_neighborhoods:
                        ok = True
                        size = len(neighbours)
                        es = edge_set
                        nn = n

                        for i in range(size - 1):
                            u = neighbours[i]
                            base = u * nn
                            for j in range(i + 1, size):
                                if base + neighbours[j] not in es:
                                    ok = False
                                    break
                            if not ok:
                                break

                        if ok:
                            found_clique = [v] + neighbours
                            break
                        else:
                            failed_neighborhoods.add(key)

            removed[v] = 1
            active_count -= 1

            for u in adj[v]:
                if not removed[u]:
                    degree[u] -= 1
                    if degree[u] < k:
                        queue.append(u)

        if found_clique is not None:
            output.append("2")
            output.append(" ".join(str(x + 1) for x in found_clique))
        else:
            if active_count > 0:
                answer = [str(i + 1) for i in range(n) if not removed[i]]
                output.append("1 " + str(len(answer)))
                output.append(" ".join(answer))
            else:
                output.append("-1")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()