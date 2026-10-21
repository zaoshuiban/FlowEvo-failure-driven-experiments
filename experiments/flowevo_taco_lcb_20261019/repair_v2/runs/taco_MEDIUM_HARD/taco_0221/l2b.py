import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    parent = [0] * (n + 1)
    c = [0] * (n + 1)
    children = [[] for _ in range(n + 1)]

    idx = 1
    root = 0

    for v in range(1, n + 1):
        p = data[idx]
        ci = data[idx + 1]
        idx += 2

        parent[v] = p
        c[v] = ci

        if p == 0:
            root = v
        else:
            children[p].append(v)

    sys.setrecursionlimit(10000)

    subtree_size = [0] * (n + 1)
    order = [None] * (n + 1)
    possible = True

    def dfs(u: int) -> None:
        nonlocal possible

        descendants = []
        size = 1

        for v in children[u]:
            dfs(v)
            size += subtree_size[v]
            descendants.extend(order[v])

        subtree_size[u] = size

        if c[u] < 0 or c[u] > size - 1:
            possible = False
            pos = min(max(c[u], 0), len(descendants))
        else:
            pos = c[u]

        descendants.insert(pos, u)
        order[u] = descendants

    if root == 0:
        print("NO")
        return

    dfs(root)

    if not possible or len(order[root]) != n:
        print("NO")
        return

    answer = [0] * (n + 1)

    for value, vertex in enumerate(order[root], start=1):
        answer[vertex] = value

    print("YES")
    print(*answer[1:])


if __name__ == "__main__":
    solve()