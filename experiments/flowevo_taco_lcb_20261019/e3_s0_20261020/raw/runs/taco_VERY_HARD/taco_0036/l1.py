import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    c = [next(it) for _ in range(n)]

    u = [0] * m
    v = [0] * m
    adj = [[] for _ in range(n)]

    for i in range(m):
        a = next(it) - 1
        b = next(it) - 1
        u[i] = a
        v[i] = b
        adj[a].append((b, i))
        adj[b].append((a, i))

    parent = [-2] * n
    parent_edge = [-1] * n
    parity = [0] * n
    order = []

    root = 0
    parent[root] = -1
    stack = [root]

    while stack:
        x = stack.pop()
        order.append(x)

        for y, eid in adj[x]:
            if parent[y] == -2:
                parent[y] = x
                parent_edge[y] = eid
                parity[y] = parity[x] ^ 1
                stack.append(y)

    is_tree = [False] * m
    for x in range(n):
        if parent[x] >= 0:
            is_tree[parent_edge[x]] = True

    special = -1
    su = sv = -1

    for eid in range(m):
        if not is_tree[eid]:
            a = u[eid]
            b = v[eid]
            if parity[a] == parity[b]:
                special = eid
                su = a
                sv = b
                break

    base = [0] * m
    coef = [0] * m

    acc_base = [0] * n
    acc_coef = [0] * n

    for x in reversed(order):
        if x == root:
            continue

        inc = 1 if special != -1 and (x == su or x == sv) else 0

        eid = parent_edge[x]
        b = c[x] - acc_base[x]
        co = -(acc_coef[x] + inc)

        base[eid] = b
        coef[eid] = co

        p = parent[x]
        acc_base[p] += b
        acc_coef[p] += co

    inc_root = 1 if special != -1 and (root == su or root == sv) else 0

    b_root = acc_base[root]
    a_root = acc_coef[root] + inc_root
    residual = c[root] - b_root

    if special == -1:
        if residual != 0:
            print("NO")
            return
        x_value = 0
    else:
        if a_root == 0:
            if residual != 0:
                print("NO")
                return
            x_value = 0
        else:
            if residual % a_root != 0:
                print("NO")
                return
            x_value = residual // a_root

    answer = []

    for eid in range(m):
        if eid == special:
            w = x_value
        else:
            w = base[eid] + coef[eid] * x_value
        answer.append(str(w))

    sys.stdout.write("YES\n" + "\n".join(answer))


if __name__ == "__main__":
    solve()