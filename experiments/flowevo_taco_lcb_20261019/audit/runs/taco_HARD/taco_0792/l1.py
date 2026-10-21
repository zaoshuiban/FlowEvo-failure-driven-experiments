import sys

def solve():
    input = sys.stdin.buffer.readline
    first = input().split()
    if not first:
        return

    n, e = map(int, first)

    adj = [[] for _ in range(n + 1)]
    deg = [0] * (n + 1)

    for i in range(e):
        a, b = map(int, input().split())
        adj[a].append((b, i))
        adj[b].append((a, i))
        deg[a] += 1
        deg[b] += 1

    # For an Eulerian directed graph, every vertex must have even degree
    # in the underlying undirected graph.
    for i in range(1, n + 1):
        if deg[i] & 1:
            sys.stdout.write("NO\n")
            return

    # The underlying undirected graph must be connected.
    visited = [False] * (n + 1)
    visited[1] = True
    stack = [1]
    count = 0

    while stack:
        x = stack.pop()
        count += 1
        for y, _ in adj[x]:
            if not visited[y]:
                visited[y] = True
                stack.append(y)

    if count != n:
        sys.stdout.write("NO\n")
        return

    # Orient edges along an Euler tour of the undirected graph.
    used = [False] * e
    ptr = [0] * (n + 1)
    ans_u = [0] * e
    ans_v = [0] * e

    stack = [1]

    while stack:
        x = stack[-1]

        while ptr[x] < len(adj[x]) and used[adj[x][ptr[x]][1]]:
            ptr[x] += 1

        if ptr[x] == len(adj[x]):
            stack.pop()
        else:
            y, eid = adj[x][ptr[x]]
            ptr[x] += 1

            used[eid] = True
            ans_u[eid] = x
            ans_v[eid] = y
            stack.append(y)

    output = ["YES\n"]
    for i in range(e):
        output.append(f"{ans_u[i]} {ans_v[i]}\n")

    sys.stdout.write("".join(output))


if __name__ == "__main__":
    solve()