import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    adj = [[False] * n for _ in range(n)]
    degree = [0] * n

    pos = 2
    for _ in range(m):
        u = data[pos] - 1
        v = data[pos + 1] - 1
        pos += 2

        adj[u][v] = adj[v][u] = True
        degree[u] += 1
        degree[v] += 1

    # Complete graph can always be represented using only letter 'a'.
    if all(degree[i] == n - 1 for i in range(n)):
        print("Yes")
        print("a" * n)
        return

    labels = ['?'] * n

    # In a non-complete valid graph, vertices of degree n - 1 must be 'b'.
    for i in range(n):
        if degree[i] == n - 1:
            labels[i] = 'b'

    visited = [False] * n
    component = [-1] * n
    comp_id = 0

    # The remaining graph must split into two cliques: vertices with 'a' and 'c'.
    for start in range(n):
        if labels[start] != '?' or visited[start]:
            continue

        stack = [start]
        visited[start] = True

        while stack:
            v = stack.pop()
            component[v] = comp_id

            for to in range(n):
                if (
                    labels[to] == '?'
                    and not visited[to]
                    and adj[v][to]
                ):
                    visited[to] = True
                    stack.append(to)

        comp_id += 1

    for i in range(n):
        if labels[i] == '?':
            labels[i] = 'a' if component[i] == 0 else 'c'

    value = {'a': 0, 'b': 1, 'c': 2}

    ok = True
    for i in range(n):
        for j in range(i + 1, n):
            should_be_edge = abs(value[labels[i]] - value[labels[j]]) <= 1
            if should_be_edge != adj[i][j]:
                ok = False
                break
        if not ok:
            break

    if ok:
        print("Yes")
        print("".join(labels))
    else:
        print("No")


if __name__ == "__main__":
    solve()