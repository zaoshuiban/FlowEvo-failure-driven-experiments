import sys

def main():
    sys.setrecursionlimit(10**7)
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)

    parent = [0] * (n + 1)
    c = [0] * (n + 1)
    children = [[] for _ in range(n + 1)]

    root = 0
    for v in range(1, n + 1):
        p = next(it)
        cv = next(it)
        parent[v] = p
        c[v] = cv
        if p == 0:
            root = v
        else:
            children[p].append(v)

    size = [0] * (n + 1)

    def calc_size(v):
        total = 1
        for u in children[v]:
            total += calc_size(u)
        size[v] = total
        return total

    calc_size(root)

    for v in range(1, n + 1):
        if c[v] >= size[v]:
            print("NO")
            return

    def build_order(v):
        order = []
        for u in children[v]:
            order.extend(build_order(u))

        order.insert(c[v], v)
        return order

    order = build_order(root)

    ans = [0] * (n + 1)
    for rank, v in enumerate(order, start=1):
        ans[v] = rank

    print("YES")
    print(*ans[1:])


if __name__ == "__main__":
    main()