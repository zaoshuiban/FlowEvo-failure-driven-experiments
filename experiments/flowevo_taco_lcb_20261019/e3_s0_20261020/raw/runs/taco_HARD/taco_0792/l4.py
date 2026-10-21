import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    e = next(it)

    adj = [[] for _ in range(n)]

    for i in range(e):
        a = next(it) - 1
        b = next(it) - 1
        adj[a].append((b, i))
        adj[b].append((a, i))

    if e == 0:
        if n <= 1:
            sys.stdout.write("YES\n")
        else:
            sys.stdout.write("NO\n")
        return

    # An Eulerian orientation exists iff every vertex has even degree
    # and the underlying undirected graph is connected.
    for v in range(n):
        if len(adj[v]) & 1:
            sys.stdout.write("NO\n")
            return

    if n > 1:
        for v in range(n):
            if not adj[v]:
                sys.stdout.write("NO\n")
                return

        seen = bytearray(n)
        stack = [0]
        seen[0] = 1
        count = 1

        while stack:
            v = stack.pop()
            for to, _ in adj[v]:
                if not seen[to]:
                    seen[to] = 1
                    count += 1
                    stack.append(to)

        if count != n:
            sys.stdout.write("NO\n")
            return

    used = bytearray(e)
    ptr = [0] * n
    stack = [0]

    out_u = [0] * e
    out_v = [0] * e

    while stack:
        v = stack[-1]
        p = ptr[v]

        while p < len(adj[v]) and used[adj[v][p][1]]:
            p += 1

        ptr[v] = p

        if p == len(adj[v]):
            stack.pop()
        else:
            to, edge_id = adj[v][p]
            ptr[v] = p + 1
            used[edge_id] = 1

            out_u[edge_id] = v + 1
            out_v[edge_id] = to + 1

            stack.append(to)

    if sum(used) != e:
        sys.stdout.write("NO\n")
        return

    ans = ["YES"]
    ans.extend(f"{out_u[i]} {out_v[i]}" for i in range(e))
    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()