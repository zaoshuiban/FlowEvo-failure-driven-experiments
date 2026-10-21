import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    out = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        k = data[idx + 2]
        idx += 3

        # Any single vertex is a clique of size 1.
        if k == 1:
            idx += 2 * m
            out.append("2")
            out.append("1")
            continue

        # Any edge is a clique of size 2.
        if k == 2:
            first_u = -1
            first_v = -1
            for _ in range(m):
                u = data[idx] - 1
                v = data[idx + 1] - 1
                idx += 2
                if first_u == -1:
                    first_u = u
                    first_v = v

            if first_u == -1:
                out.append("-1")
            else:
                out.append("2")
                out.append(f"{first_u + 1} {first_v + 1}")
            continue

        adj = [set() for _ in range(n)]

        for _ in range(m):
            u = data[idx] - 1
            v = data[idx + 1] - 1
            idx += 2
            adj[u].add(v)
            adj[v].add(u)

        # If k * (k - 1) / 2 > m, a k-clique cannot exist.
        check_clique = (k * (k - 1) // 2 <= m)

        queue = []
        for v in range(n):
            if len(adj[v]) < k:
                queue.append(v)

        removed = [False] * n
        active = n
        head = 0
        found_clique = None

        target_inside = k - 2

        while head < len(queue):
            v = queue[head]
            head += 1

            if removed[v]:
                continue

            neighbors = adj[v]

            if check_clique and len(neighbors) == k - 1:
                ok = True

                for u in neighbors:
                    if len(adj[u].intersection(neighbors)) != target_inside:
                        ok = False
                        break

                if ok:
                    found_clique = [v]
                    found_clique.extend(neighbors)
                    break

            removed[v] = True
            active -= 1

            for u in neighbors:
                adj[u].remove(v)

                if len(adj[u]) == k - 1:
                    queue.append(u)

            neighbors.clear()

        if found_clique is not None:
            out.append("2")
            out.append(" ".join(str(v + 1) for v in found_clique))
        else:
            if active > 0:
                vertices = [str(v + 1) for v in range(n) if not removed[v]]
                out.append(f"1 {len(vertices)}")
                out.append(" ".join(vertices))
            else:
                out.append("-1")

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()