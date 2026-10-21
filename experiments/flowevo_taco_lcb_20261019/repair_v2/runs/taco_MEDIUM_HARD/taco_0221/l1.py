import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)

    children = [[] for _ in range(n)]
    c = [0] * n
    root = -1

    for i in range(n):
        p = next(it)
        ci = next(it)
        c[i] = ci

        if p == 0:
            root = i
        else:
            children[p - 1].append(i)

    order = []
    stack = [root]

    while stack:
        u = stack.pop()
        order.append(u)
        for v in children[u]:
            stack.append(v)

    subtree_order = [None] * n
    possible = True

    for u in reversed(order):
        desc = []
        for v in children[u]:
            desc.extend(subtree_order[v])

        if c[u] < 0 or c[u] > len(desc):
            possible = False
            break

        desc.insert(c[u], u)
        subtree_order[u] = desc

    if not possible:
        print("NO")
        return

    ans = [0] * n
    for value, vertex in enumerate(subtree_order[root], start=1):
        ans[vertex] = value

    print("YES")
    print(*ans)


if __name__ == "__main__":
    main()