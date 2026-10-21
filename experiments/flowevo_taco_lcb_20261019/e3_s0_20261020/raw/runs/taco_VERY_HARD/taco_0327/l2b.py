```python
import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    adj = [[] for _ in range(n)]
    p = 1
    for _ in range(n - 1):
        u = data[p] - 1
        v = data[p + 1] - 1
        p += 2
        adj[u].append(v)
        adj[v].append(u)

    deg = [len(x) for x in adj]
    marked = [d >= 3 for d in deg]

    def farthest_marked(s, need_parent=False):
        parent = [-1] * n
        depth = [0] * n
        order = [s]

        best = s
        maxd = -1

        idx = 0
        while idx < len(order):
            v = order[idx]
            idx += 1

            dv = depth[v]
            if marked[v] and dv > maxd:
                maxd = dv
                best = v

            for u in adj[v]:
                if u == parent[v]:
                    continue
                parent[u] = v
                depth[u] = dv + 1
                order.append(u)

        if need_parent:
            return best, maxd, parent
        return best, maxd

    start = 0
    while not marked[start]:
        start += 1

    a, _ = farthest_marked(start)
    b, D, parent = farthest_marked(a, need_parent=True)

    path = []
    cur = b
    while True:
        path.append(cur)
        if cur == a:
            break
        cur = parent[cur]
    path.reverse()

    def best_in_component(root, blocked, target_depth):
        parent = [-1] * n
        depth = [0] * n
        order = [root]

        parent[root] = blocked

        idx = 0
        while idx < len(order):
            v = order[idx]
            idx += 1

            for u in adj[v]:
                if u == parent[v]:
                    continue
                parent[u] = v
                depth[u] = depth[v] + 1
                order.append(u)

        height = [0] * n
        far = [0] * n

        best_val = -1
        best_v = -1
        best_e1 = -1
        best_e2 = -1

        for v in reversed(order):
            b1 = b2 = 0
            e1 = e2 = -1

            for u in adj[v]:
                if parent[u] == v:
                    length = height[u] + 1
                    endpoint = far[u]

                    if length > b1:
                        b2, e2 = b1, e1
                        b1, e1 = length, endpoint
                    elif length > b2:
                        b2, e2 = length, endpoint

            height[v] = b1
            far[v] = e1 if b1 > 0 else v

            if depth[v] == target_depth and deg[v] >= 3:
                val = b1 + b2
                if val > best_val:
                    best_val = val
                    best_v = v
                    best_e1 = e1
                    best_e2 = e2

        return best_val, best_v, best_e1, best_e2

    def best_two_components(center, target_depth):
        parent = [-1] * n
        depth = [0] * n
        comp = [-1] * n
        order = [center]

        idx = 0
        while idx < len(order):
            v = order[idx]
            idx += 1

            for u in adj[v]:
                if u == parent[v]:
                    continue

                parent[u] = v
                depth[u] = depth[v] + 1

                if v == center:
                    comp[u] = u
                else:
                    comp[u] = comp[v]

                order.append(u)

        height = [0] * n
        far = [0] * n
        best_by_component = {}

        for v in reversed(order):
            b1 = b2 = 0
            e1 = e2 = -1

            for u in adj[v]:
                if parent[u] == v:
                    length = height[u] + 1
                    endpoint = far[u]

                    if length > b1:
                        b2, e2 = b1, e1
                        b1, e1 = length, endpoint
                    elif length > b2:
                        b2, e2 = length, endpoint

            height[v] = b1
            far[v] = e1 if b1 > 0 else v

            if depth[v] == target_depth and deg[v] >= 3:
                cid = comp[v]
                val = b1 + b2
                old = best_by_component.get(cid)

                if old is None or val > old[0]:
                    best_by_component[cid] = (val, v, e1, e2)

        best1 = None
        best2 = None

        for item in best_by_component.values():
            if best1 is None or item[0] > best1[0]:
                best2 = best1
                best1 = item
            elif best2 is None or item[0] > best2[0]:
                best2 = item

        return best1, best2

    if D % 2 == 0:
        center = path[D // 2]
        radius = D // 2

        info1, info2 = best_two