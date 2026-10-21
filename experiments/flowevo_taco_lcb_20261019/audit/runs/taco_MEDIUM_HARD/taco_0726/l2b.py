import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    adj = [[False] * n for _ in range(n)]

    for _ in range(m):
        u = next(it) - 1
        v = next(it) - 1
        adj[u][v] = adj[v][u] = True

    # Find any non-edge. A non-edge can only appear between letters 'a' and 'c'.
    u = v = -1
    for i in range(n):
        for j in range(i + 1, n):
            if not adj[i][j]:
                u, v = i, j
                break
        if u != -1:
            break

    # The graph is complete, so all vertices can have the same letter.
    if u == -1:
        print("Yes")
        print("a" * n)
        return

    labels = ['?'] * n
    labels[u] = 'a'
    labels[v] = 'c'

    ok = True

    for w in range(n):
        if w == u or w == v:
            continue

        # w is not connected to u, so w must be 'c'.
        if not adj[u][w]:
            labels[w] = 'c'
            if not adj[v][w]:
                ok = False
                break
        else:
            # w is not connected to v, so w must be 'a'.
            if not adj[v][w]:
                labels[w] = 'a'
            else:
                labels[w] = 'b'

    if ok:
        value = {'a': 0, 'b': 1, 'c': 2}

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