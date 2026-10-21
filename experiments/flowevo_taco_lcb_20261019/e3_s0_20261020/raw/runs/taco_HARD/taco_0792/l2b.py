import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    e = next(it)

    adj = [[] for _ in range(n)]
    degree = [0] * n

    parent = list(range(n))
    size = [1] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra = find(a)
        rb = find(b)
        if ra == rb:
            return
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]

    for edge_id in range(e):
        a = next(it) - 1
        b = next(it) - 1

        adj[a].append((b, edge_id))
        adj[b].append((a, edge_id))

        degree[a] += 1
        degree[b] += 1

        union(a, b)

    possible = True

    for d in degree:
        if d & 1:
            possible = False
            break

    if possible:
        root = find(0)
        for i in range(1, n):
            if find(i) != root:
                possible = False
                break

    if not possible:
        sys.stdout.write("NO\n")
        return

    used = bytearray(e)
    ptr = [0] * n

    answer_u = [0] * e
    answer_v = [0] * e

    start = 0
    stack = [start]

    while stack:
        v = stack[-1]
        current_adj = adj[v]

        while ptr[v] < len(current_adj) and used[current_adj[ptr[v]][1]]:
            ptr[v] += 1

        if ptr[v] < len(current_adj):
            to, edge_id = current_adj[ptr[v]]
            ptr[v] += 1

            used[edge_id] = 1
            answer_u[edge_id] = v + 1
            answer_v[edge_id] = to + 1

            stack.append(to)
        else:
            stack.pop()

    output = ["YES"]
    output.extend(f"{answer_u[i]} {answer_v[i]}" for i in range(e))

    sys.stdout.write("\n".join(output))
    sys.stdout.write("\n")


if __name__ == "__main__":
    solve()