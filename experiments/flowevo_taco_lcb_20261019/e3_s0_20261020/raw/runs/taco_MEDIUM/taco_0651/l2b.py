import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    adj = [[] for _ in range(n + 1)]

    idx = 2
    for _ in range(m):
        u, v = data[idx], data[idx + 1]
        idx += 2
        adj[u].append(v)
        adj[v].append(u)

    parent = [0] * (n + 1)
    parent[1] = -1
    order = [1]

    for u in order:
        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)

    subtree_size = [1] * (n + 1)
    removed_edges = 0

    for u in reversed(order):
        if u != 1:
            if subtree_size[u] % 2 == 0:
                removed_edges += 1
            subtree_size[parent[u]] += subtree_size[u]

    print(removed_edges)


if __name__ == "__main__":
    main()