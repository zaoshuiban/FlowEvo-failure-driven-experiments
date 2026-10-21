import sys
from bisect import bisect_left

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    idx = 1

    a = [0] * (n + 1)
    for i in range(1, n + 1):
        a[i] = data[idx]
        idx += 1

    children = [[] for _ in range(n + 1)]
    parent = [0] * (n + 1)
    edge_weight = [0] * (n + 1)

    for child in range(2, n + 1):
        p = data[idx]
        w = data[idx + 1]
        idx += 2

        parent[child] = p
        edge_weight[child] = w
        children[p].append(child)

    diff = [0] * (n + 1)
    order = []

    path_nodes = []
    path_dists = []

    stack = [(1, 0)]

    while stack:
        u, state = stack.pop()

        if state == 0:
            if u == 1:
                dist_u = 0
            else:
                dist_u = path_dists[-1] + edge_weight[u]

            path_nodes.append(u)
            path_dists.append(dist_u)

            depth = len(path_nodes) - 1

            if u != 1:
                pos = bisect_left(path_dists, dist_u - a[u])

                if pos < depth:
                    diff[path_nodes[depth - 1]] += 1

                    if pos > 0:
                        diff[path_nodes[pos - 1]] -= 1

            order.append(u)

            stack.append((u, 1))

            ch = children[u]
            for i in range(len(ch) - 1, -1, -1):
                stack.append((ch[i], 0))

        else:
            path_nodes.pop()
            path_dists.pop()

    for u in reversed(order):
        if u != 1:
            diff[parent[u]] += diff[u]

    sys.stdout.write(" ".join(str(diff[i]) for i in range(1, n + 1)))


if __name__ == "__main__":
    solve()