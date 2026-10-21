import sys


def solve() -> None:
    input = sys.stdin.buffer.readline

    n = int(input())
    adj = [[] for _ in range(n)]

    for _ in range(n - 1):
        u, v = map(int, input().split())
        u -= 1
        v -= 1
        adj[u].append(v)
        adj[v].append(u)

    special = [i for i in range(n) if len(adj[i]) >= 3]

    def farthest_special(start):
        parent = [-1] * n
        dist = [0] * n
        parent[start] = -2

        stack = [start]
        while stack:
            u = stack.pop()
            du = dist[u]
            for v in adj[u]:
                if v == parent[u]:
                    continue
                parent[v] = u
                dist[v] = du + 1
                stack.append(v)

        best = start
        best_dist = -1
        for v in special:
            if dist[v] > best_dist:
                best_dist = dist[v]
                best = v

        return best, best_dist, parent

    start = special[0]
    u, _, tmp_parent = farthest_special(start)
    del tmp_parent

    v, diameter, parent = farthest_special(u)

    path = []
    cur = v
    while True:
        path.append(cur)
        if cur == u:
            break
        cur = parent[cur]
    path.reverse()

    if diameter % 2 == 0:
        center = path[diameter // 2]
        radius = diameter // 2

        del parent, path

        par = [-1] * n
        depth = [0] * n
        branch = [-1] * n
        order = []

        par[center] = -2
        stack = [center]

        while stack:
            x = stack.pop()
            order.append(x)

            for y in adj[x]:
                if y == par[x]:
                    continue

                par[y] = x
                depth[y] = depth[x] + 1

                if x == center:
                    branch[y] = y
                else:
                    branch[y] = branch[x]

                stack.append(y)

        down_len = [0] * n
        down_leaf = [0] * n

        best_by_branch = {}

        for x in reversed(order):
            best1 = 0
            best2 = 0
            leaf1 = -1
            leaf2 = -1

            for y in adj[x]:
                if y == par[x]:
                    continue

                length = 1 + down_len[y]
                leaf = down_leaf[y]

                if length > best1:
                    best2 = best1
                    leaf2 = leaf1
                    best1 = length
                    leaf1 = leaf
                elif length > best2:
                    best2 = length
                    leaf2 = leaf

            down_len[x] = best1
            if best1 > 0:
                down_leaf[x] = leaf1
            else:
                down_leaf[x] = x

            if depth[x] == radius and best2 > 0:
                score = best1 + best2
                br = branch[x]

                old = best_by_branch.get(br)
                if old is None or score > old[0]:
                    best_by_branch[br] = (score, x, leaf1, leaf2)

        best_a = None
        best_b = None

        for cand in best_by_branch.values():
            if best_a is None or cand[0] > best_a[0]:
                best_b = best_a
                best_a = cand
            elif best_b is None or cand[0] > best_b[0]:
                best_b = cand

        A, A1, A2 = best_a[1], best_a[2], best_a[3]
        B, B1, B2 = best_b[1], best_b[2], best_b[3]

    else:
        idx = diameter // 2
        c1 = path[idx]
        c2 = path[idx + 1]
        radius = idx

        del parent, path

        def process_side(root, blocked, target_depth):
            par = [-1] * n
            depth = [0] * n
            order = []

            par[root] = -2
            stack = [root]

            while stack:
                x = stack.pop()
                order.append(x)

                for y in adj[x]:
                    if y == blocked or y == par[x]:
                        continue

                    par[y] = x
                    depth[y] = depth[x] + 1
                    stack.append(y)

            down_len = [0] * n
            down_leaf = [0] * n

            best = None

            for x in reversed(order):
                best1 = 0
                best2 = 0
                leaf1 = -1
                leaf2 = -1

                for y in adj[x]:
                    if y == blocked or y == par[x]:
                        continue

                    length = 1 + down_len[y]
                    leaf = down_leaf[y]

                    if length > best1:
                        best2 = best1
                        leaf2 = leaf1
                        best1 = length
                        leaf1 = leaf
                    elif length > best2:
                        best2 = length
                        leaf2 = leaf

                down_len[x] = best1
                if best1 > 0:
                    down_leaf[x] = leaf1
                else:
                    down_leaf[x] = x

                if depth[x] == target_depth and best2 > 0:
                    score = best1 + best2
                    if best is None or score > best[0]:
                        best = (score, x, leaf1, leaf2)

            return best

        best_left = process_side(c1, c2, radius)
        best_right = process_side(c2, c1, radius)

        A, A1, A2 = best_left[1], best_left[2], best_left[3]
        B, B1, B2 = best_right[1], best_right[2], best_right[3]

    print(A1 + 1, B1 + 1)
    print(A2 + 1, B2 + 1)


if __name__ == "__main__":
    solve()