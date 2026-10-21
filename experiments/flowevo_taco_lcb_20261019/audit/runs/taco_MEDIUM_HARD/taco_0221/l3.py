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
    root = -1

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

    if root == -1:
        print("NO")
        return

    # Get an order where every child appears before its parent.
    stack = [root]
    preorder = []
    while stack:
        u = stack.pop()
        preorder.append(u)
        for v in children[u]:
            stack.append(v)

    rev_preorder = preorder[::-1]

    # Compute subtree sizes.
    size = [1] * (n + 1)
    for u in rev_preorder:
        for v in children[u]:
            size[u] += size[v]

    # Check whether all c_i are possible.
    for u in range(1, n + 1):
        if c[u] < 0 or c[u] >= size[u]:
            print("NO")
            return

    # Build the increasing-by-a order for every subtree.
    order = [None] * (n + 1)

    for u in rev_preorder:
        lst = []
        for v in children[u]:
            lst.extend(order[v])
        lst.insert(c[u], u)
        order[u] = lst

    final_order = order[root]

    if len(final_order) != n:
        print("NO")
        return

    answer = [0] * (n + 1)
    for value, vertex in enumerate(final_order, start=1):
        answer[vertex] = value

    print("YES")
    print(*answer[1:])


if __name__ == "__main__":
    solve()