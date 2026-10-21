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
    order = [0]

    for u in order:
        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)

    expected = [0.0] * n

    for u in reversed(order):
        child_count = 0
        total = 0.0

        for v in adj[u]:
            if v != parent[u]:
                child_count += 1
                total += expected[v]

        if child_count > 0:
            expected[u] = 1.0 + total / child_count

    print(f"{expected[0]:.15f}")


if __name__ == "__main__":
    main()