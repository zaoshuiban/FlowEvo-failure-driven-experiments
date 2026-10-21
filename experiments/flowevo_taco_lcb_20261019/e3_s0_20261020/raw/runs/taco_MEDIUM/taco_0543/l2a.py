import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    adj = [[] for _ in range(n)]

    idx = 1
    for _ in range(n - 1):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        adj[u].append(v)
        adj[v].append(u)

    parent = [-1] * n
    order = []
    stack = [0]

    while stack:
        u = stack.pop()
        order.append(u)

        for v in adj[u]:
            if v == parent[u]:
                continue
            parent[v] = u
            stack.append(v)

    children_count = [0] * n
    total_expected = [0.0] * n
    expected = [0.0] * n

    for u in reversed(order):
        if children_count[u] > 0:
            expected[u] = total_expected[u] / children_count[u]
        else:
            expected[u] = 0.0

        p = parent[u]
        if p != -1:
            total_expected[p] += 1.0 + expected[u]
            children_count[p] += 1

    print(f"{expected[0]:.15f}")


if __name__ == "__main__":
    main()