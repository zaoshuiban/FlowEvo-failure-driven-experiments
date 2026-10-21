import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    k = next(it)

    adj = [[] for _ in range(n)]
    for _ in range(n - 1):
        u = next(it) - 1
        v = next(it) - 1
        adj[u].append(v)
        adj[v].append(u)

    parent = [-1] * n
    depth = [0] * n
    order = [0]
    parent[0] = -2

    for v in order:
        for to in adj[v]:
            if to == parent[v]:
                continue
            parent[to] = v
            depth[to] = depth[v] + 1
            order.append(to)

    subtree_size = [1] * n

    for v in reversed(order[1:]):
        subtree_size[parent[v]] += subtree_size[v]

    values = [depth[i] - subtree_size[i] + 1 for i in range(n)]
    values.sort(reverse=True)

    print(sum(values[:k]))

if __name__ == "__main__":
    main()