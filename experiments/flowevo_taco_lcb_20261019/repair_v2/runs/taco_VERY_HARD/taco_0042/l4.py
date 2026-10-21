import sys
from collections import deque


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    output = []

    for _ in range(t):
        n = next_int()
        m = next_int()
        k = next_int()

        if k == 1:
            for __ in range(m):
                next_int()
                next_int()
            output.append("2")
            output.append("1")
            continue

        can_check_clique = k * (k - 1) // 2 <= m

        if can_check_clique:
            adj = [set() for _ in range(n)]

            for __ in range(m):
                u = next_int() - 1
                v = next_int() - 1
                adj[u].add(v)
                adj[v].add(u)

            deg = [len(s) for s in adj]
            alive = [True] * n
            q = deque()

            for i, d in enumerate(deg):
                if d < k:
                    q.append(i)

            remaining = n
            found_clique = None

            while q:
                v = q.popleft()

                if not alive[v] or deg[v] >= k:
                    continue

                if deg[v] == k - 1:
                    neighbors = []
                    for u in adj[v]:
                        if alive[u]:
                            neighbors.append(u)

                    if len(neighbors) == k - 1:
                        ok = True

                        for u in neighbors:
                            if deg[u] < k - 1:
                                ok = False
                                break

                        if ok:
                            neighbors.sort(key=deg.__getitem__)

                            for i in range(k - 1):
                                u = neighbors[i]
                                au = adj[u]
                                for j in range(i + 1, k - 1):
                                    if neighbors[j] not in au:
                                        ok = False
                                        break
                                if not ok:
                                    break

                        if ok:
                            found_clique = [v]
                            found_clique.extend(neighbors)
                            break

                alive[v] = False
                remaining -= 1

                for u in adj[v]:
                    if alive[u]:
                        deg[u] -= 1
                        if deg[u] < k:
                            q.append(u)

            if found_clique is not None:
                output.append("2")
                output.append(" ".join(str(x + 1) for x in found_clique))
            elif remaining > 0:
                output.append(f"1 {remaining}")
                output.append(" ".join(str(i + 1) for i in range(n) if alive[i]))
            else:
                output.append("-1")

        else:
            adj = [[] for _ in range(n)]

            for __ in range(m):
                u = next_int() - 1
                v = next_int() - 1
                adj[u].append(v)
                adj[v].append(u)

            deg = [len(x) for x in adj]
            alive = [True] * n
            q = deque()

            for i, d in enumerate(deg):
                if d < k:
                    q.append(i)

            remaining = n

            while q:
                v = q.popleft()

                if not alive[v] or deg[v] >= k:
                    continue

                alive[v] = False
                remaining -= 1

                for u in adj[v]:
                    if alive[u]:
                        deg[u] -= 1
                        if deg[u] < k:
                            q.append(u)

            if remaining > 0:
                output.append(f"1 {remaining}")
                output.append(" ".join(str(i + 1) for i in range(n) if alive[i]))
            else:
                output.append("-1")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()