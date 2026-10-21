import sys
from bisect import bisect_left


def balanced_query(n, c, adj):
    W = sum(c)

    # Iterative DFS for tin, tout, parent and preorder
    parent = [-1] * n
    parent[0] = 0

    tin = [0] * n
    tout = [0] * n
    order = []

    stack = [(0, 0)]  # (node, state), state 0 = enter, 1 = exit
    while stack:
        u, state = stack.pop()

        if state == 0:
            tin[u] = len(order)
            order.append(u)

            stack.append((u, 1))
            pu = parent[u]
            for v in adj[u]:
                if v != pu:
                    parent[v] = u
                    stack.append((v, 0))
        else:
            tout[u] = len(order)

    # subtree sums
    sub = c[:]
    for i in range(n - 1, 0, -1):
        u = order[i]
        sub[parent[u]] += sub[u]

    # Occurrences of every cuttable subtree sum, stored by tin.
    occ = {}
    for u in order:
        if u != 0:
            s = sub[u]
            occ.setdefault(s, []).append(tin[u])

    INF = 10 ** 30
    ans = INF

    # Case: cut the newly added edge and one original edge.
    if W % 2 == 0:
        S = W // 2
        if S in occ:
            ans = min(ans, S)

    # Case: two equal lower subtrees, new node added to root component.
    for s, lst in occ.items():
        if len(lst) >= 2 and 2 * s < W < 3 * s:
            ans = min(ans, 3 * s - W)

    # Case: one lower subtree and the root component are equal.
    # For a subtree sum s, the third component needs sum W - 2*s,
    # and it must be outside this subtree.
    for u in order:
        if u == 0:
            continue

        s = sub[u]
        t = W - 2 * s

        if t > 0 and t < s:
            lst = occ.get(t)
            if lst is not None:
                total = len(lst)
                left = bisect_left(lst, tin[u])
                right = bisect_left(lst, tout[u])
                inside = right - left

                if total > inside:
                    ans = min(ans, s - t)

    # Cases where the two cuts are on the same root-to-leaf path:
    # components are: deep subtree d, middle part, and root remainder.
    anc = {}
    stack = [(0, 0)]

    while stack:
        u, state = stack.pop()

        if state == 0:
            if u != 0:
                d = sub[u]

                # deep == middle, with ancestor subtree sum 2*d
                # deep == root, with ancestor subtree sum W-d
                if 2 * d < W < 3 * d:
                    cand = 3 * d - W

                    if anc.get(2 * d, 0):
                        ans = min(ans, cand)

                    if anc.get(W - d, 0):
                        ans = min(ans, cand)

                # middle == root
                if W > 3 * d and ((W + d) & 1) == 0:
                    need = (W + d) // 2
                    if anc.get(need, 0):
                        ans = min(ans, (W - 3 * d) // 2)

                anc[d] = anc.get(d, 0) + 1

            stack.append((u, 1))
            pu = parent[u]
            for v in adj[u]:
                if v != pu:
                    stack.append((v, 0))

        else:
            if u != 0:
                d = sub[u]
                anc[d] -= 1
                if anc[d] == 0:
                    del anc[d]

    return -1 if ans == INF else ans


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    q = data[idx]
    idx += 1

    answers = []

    for _ in range(q):
        n = data[idx]
        idx += 1

        c = data[idx:idx + n]
        idx += n

        adj = [[] for _ in range(n)]

        for _ in range(n - 1):
            x = data[idx] - 1
            y = data[idx + 1] - 1
            idx += 2

            adj[x].append(y)
            adj[y].append(x)

        answers.append(str(balanced_query(n, c, adj)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()