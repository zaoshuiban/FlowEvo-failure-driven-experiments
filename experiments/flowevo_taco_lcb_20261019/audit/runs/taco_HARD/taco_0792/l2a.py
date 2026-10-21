import sys


def solve() -> None:
    data = sys.stdin.buffer.read()

    def ints():
        num = 0
        in_num = False
        for c in data:
            if 48 <= c <= 57:
                num = num * 10 + (c - 48)
                in_num = True
            elif in_num:
                yield num
                num = 0
                in_num = False
        if in_num:
            yield num

    it = ints()
    try:
        n = next(it)
    except StopIteration:
        return
    e = next(it)

    u = [0] * e
    v = [0] * e

    adj = [[] for _ in range(n + 1)]
    degree = [0] * (n + 1)

    for edge_id in range(e):
        a = next(it)
        b = next(it)
        u[edge_id] = a
        v[edge_id] = b

        adj[a].append((b, edge_id))
        adj[b].append((a, edge_id))

        degree[a] += 1
        degree[b] += 1

    # An Eulerian orientation exists only if every degree is even.
    for city in range(1, n + 1):
        if degree[city] & 1:
            sys.stdout.write("NO\n")
            return

    if e == 0:
        sys.stdout.write("YES\n" if n == 1 else "NO\n")
        return

    # Find a non-isolated starting city.
    start = 1
    while start <= n and degree[start] == 0:
        start += 1

    # The underlying undirected graph must connect all cities.
    visited = [False] * (n + 1)
    stack = [start]
    visited[start] = True
    visited_count = 0

    while stack:
        city = stack.pop()
        visited_count += 1

        for nxt, _ in adj[city]:
            if not visited[nxt]:
                visited[nxt] = True
                stack.append(nxt)

    if visited_count != n:
        sys.stdout.write("NO\n")
        return

    # Hierholzer's algorithm for an undirected Euler circuit.
    used = bytearray(e)
    ptr = [0] * (n + 1)

    vertex_stack = [start]
    edge_stack = [-1]
    popped_edges = []

    while vertex_stack:
        city = vertex_stack[-1]
        av = adj[city]
        p = ptr[city]

        while p < len(av) and used[av[p][1]]:
            p += 1

        ptr[city] = p

        if p < len(av):
            nxt, edge_id = av[p]
            used[edge_id] = 1
            ptr[city] = p + 1

            vertex_stack.append(nxt)
            edge_stack.append(edge_id)
        else:
            vertex_stack.pop()
            edge_id = edge_stack.pop()

            if edge_id != -1:
                popped_edges.append(edge_id)

    if len(popped_edges) != e:
        sys.stdout.write("NO\n")
        return

    # Reverse the popped edge order to get an Euler circuit.
    answer_u = [0] * e
    answer_v = [0] * e

    current = start

    for idx in range(e - 1, -1, -1):
        edge_id = popped_edges[idx]
        a = u[edge_id]
        b = v[edge_id]

        if current == a:
            answer_u[edge_id] = a
            answer_v[edge_id] = b
            current = b
        else:
            answer_u[edge_id] = b
            answer_v[edge_id] = a
            current = a

    output = ["YES"]
    output.extend(f"{answer_u[i]} {answer_v[i]}" for i in range(e))
    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()