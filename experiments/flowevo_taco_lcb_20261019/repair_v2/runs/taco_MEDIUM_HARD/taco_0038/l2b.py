import sys


def main():
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
    order = []
    stack = [0]
    parent[0] = -2

    while stack:
        u = stack.pop()
        order.append(u)

        for v in adj[u]:
            if v == parent[u]:
                continue
            parent[v] = u
            depth[v] = depth[u] + 1
            stack.append(v)

    subtree_size = [1] * n

    for u in reversed(order):
        if parent[u] >= 0:
            subtree_size[parent[u]] += subtree_size[u]

    values = [
        depth[i] - subtree_size[i] + 1
        for i in range(n)
    ]

    values.sort(reverse=True)

    print(sum(values[:k]))


if __name__ == "__main__":
    main()