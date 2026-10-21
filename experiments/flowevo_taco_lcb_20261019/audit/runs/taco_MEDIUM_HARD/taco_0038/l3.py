import sys


def main():
    input = sys.stdin.buffer.readline
    n, k = map(int, input().split())

    graph = [[] for _ in range(n)]
    for _ in range(n - 1):
        u, v = map(int, input().split())
        u -= 1
        v -= 1
        graph[u].append(v)
        graph[v].append(u)

    parent = [-1] * n
    depth = [0] * n
    parent[0] = 0

    order = []
    stack = [0]

    while stack:
        u = stack.pop()
        order.append(u)

        for v in graph[u]:
            if parent[v] == -1:
                parent[v] = u
                depth[v] = depth[u] + 1
                stack.append(v)

    subtree_size = [1] * n

    for u in reversed(order):
        if u != 0:
            subtree_size[parent[u]] += subtree_size[u]

    values = [depth[u] - subtree_size[u] + 1 for u in range(n)]
    values.sort(reverse=True)

    print(sum(values[:k]))


if __name__ == "__main__":
    main()