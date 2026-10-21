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

    parent = [-2] * n
    parent[0] = -1
    order = [0]

    i = 0
    while i < len(order):
        u = order[i]
        i += 1
        for v in adj[u]:
            if parent[v] == -2:
                parent[v] = u
                order.append(v)

    expected = [0.0] * n

    for u in reversed(order):
        child_count = 0
        total = 0.0

        for v in adj[u]:
            if parent[v] == u:
                child_count += 1
                total += expected[v] + 1.0

        if child_count > 0:
            expected[u] = total / child_count

    sys.stdout.write(f"{expected[0]:.15f}\n")


if __name__ == "__main__":
    main()