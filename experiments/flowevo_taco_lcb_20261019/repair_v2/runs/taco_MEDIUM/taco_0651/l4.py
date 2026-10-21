import sys

sys.setrecursionlimit(1_000_000)

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

    removed_edges = 0

    def dfs(u, parent):
        nonlocal removed_edges

        subtree_size = 1

        for v in adj[u]:
            if v == parent:
                continue
            subtree_size += dfs(v, u)

        if u != 1 and subtree_size % 2 == 0:
            removed_edges += 1

        return subtree_size

    dfs(1, 0)
    print(removed_edges)


if __name__ == "__main__":
    main()