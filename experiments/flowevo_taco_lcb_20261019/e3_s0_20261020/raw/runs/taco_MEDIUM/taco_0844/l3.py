import sys


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    idx = 0
    n = int(data[idx])
    idx += 1

    adj = [[] for _ in range(n + 1)]
    for _ in range(n - 1):
        a = int(data[idx])
        b = int(data[idx + 1])
        idx += 2
        adj[a].append(b)
        adj[b].append(a)

    parent = [0] * (n + 1)
    tin = [0] * (n + 1)
    size = [1] * (n + 1)

    parent[1] = -1
    order = []
    stack = [1]

    # Iterative DFS preorder
    while stack:
        node = stack.pop()
        tin[node] = len(order) + 1
        order.append(node)

        for nxt in adj[node]:
            if nxt != parent[node]:
                parent[nxt] = node
                stack.append(nxt)

    # Compute subtree sizes
    for node in reversed(order):
        if parent[node] > 0:
            size[parent[node]] += size[node]

    q = int(data[idx])
    idx += 1

    answers = []

    for _ in range(q):
        typ = int(data[idx])
        x = int(data[idx + 1])
        y = int(data[idx + 2])
        idx += 3

        if typ == 0:
            # Bob moves towards root from y.
            # Oliver is found if x is an ancestor of y.
            left = tin[x]
            right = tin[x] + size[x] - 1
            answers.append("YES" if left <= tin[y] <= right else "NO")
        else:
            # Bob moves away from root from y.
            # Oliver is found if x lies in the subtree of y.
            left = tin[y]
            right = tin[y] + size[y] - 1
            answers.append("YES" if left <= tin[x] <= right else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()