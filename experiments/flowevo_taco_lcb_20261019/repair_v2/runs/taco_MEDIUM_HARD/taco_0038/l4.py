import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, k = data[0], data[1]
    graph = [[] for _ in range(n + 1)]

    idx = 2
    for _ in range(n - 1):
        u = data[idx]
        v = data[idx + 1]
        idx += 2
        graph[u].append(v)
        graph[v].append(u)

    parent = [0] * (n + 1)
    depth = [0] * (n + 1)
    order = []

    stack = [1]
    parent[1] = -1

    while stack:
        u = stack.pop()
        order.append(u)

        for v in graph[u]:
            if v != parent[u]:
                parent[v] = u
                depth[v] = depth[u] + 1
                stack.append(v)

    subtree_size = [1] * (n + 1)

    for u in reversed(order):
        p = parent[u]
        if p != -1:
            subtree_size[p] += subtree_size[u]

    values = [
        depth[u] - subtree_size[u] + 1
        for u in range(1, n + 1)
    ]

    values.sort(reverse=True)
    print(sum(values[:k]))


if __name__ == "__main__":
    main()