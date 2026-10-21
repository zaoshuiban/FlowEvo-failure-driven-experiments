import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    adj = [[] for _ in range(n)]

    idx = 2
    for _ in range(n - 1):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        adj[u].append(v)
        adj[v].append(u)

    parent = [-1] * n
    depth = [0] * n
    order = [0]

    for u in order:
        for v in adj[u]:
            if v == parent[u]:
                continue
            parent[v] = u
            depth[v] = depth[u] + 1
            order.append(v)

    size = [1] * n

    for u in reversed(order):
        p = parent[u]
        if p != -1:
            size[p] += size[u]

    values = [depth[i] - size[i] + 1 for i in range(n)]
    values.sort(reverse=True)

    print(sum(values[:k]))

if __name__ == "__main__":
    solve()