import sys
from bisect import bisect_left


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = [0] * (n + 1)

    idx = 1
    for i in range(1, n + 1):
        a[i] = data[idx]
        idx += 1

    children = [[] for _ in range(n + 1)]
    parent = [0] * (n + 1)

    for v in range(2, n + 1):
        p = data[idx]
        w = data[idx + 1]
        idx += 2

        parent[v] = p
        children[p].append((v, w))

    diff = [0] * (n + 1)
    answer = [0] * (n + 1)

    path_nodes = []
    path_dist = []

    # (vertex, edge_weight_from_parent, state)
    # state = 0 -> enter, state = 1 -> exit
    stack = [(1, 0, 0)]

    while stack:
        v, w, state = stack.pop()

        if state == 0:
            dist_v = (path_dist[-1] if path_dist else 0) + w

            path_nodes.append(v)
            path_dist.append(dist_v)

            target = dist_v - a[v]
            pos = bisect_left(path_dist, target)

            diff[v] += 1
            if pos > 0:
                diff[path_nodes[pos - 1]] -= 1

            stack.append((v, w, 1))

            for i in range(len(children[v]) - 1, -1, -1):
                child, edge_weight = children[v][i]
                stack.append((child, edge_weight, 0))

        else:
            total = diff[v]
            answer[v] = total - 1

            p = parent[v]
            if p != 0:
                diff[p] += total

            path_nodes.pop()
            path_dist.pop()

    sys.stdout.write(" ".join(str(answer[i]) for i in range(1, n + 1)) + "\n")


if __name__ == "__main__":
    solve()