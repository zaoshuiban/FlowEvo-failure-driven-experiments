import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    adj = [[] for _ in range(n)]

    idx = 2
    for _ in range(m):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2
        adj[u].append(v)
        adj[v].append(u)

    color = [-1] * n

    # The graph must be bipartite. Otherwise no two disjoint vertex covers exist.
    for start in range(n):
        if color[start] != -1:
            continue

        color[start] = 0
        stack = [start]

        while stack:
            u = stack.pop()
            cu = color[u]

            for v in adj[u]:
                if color[v] == -1:
                    color[v] = cu ^ 1
                    stack.append(v)
                elif color[v] == cu:
                    sys.stdout.write("-1\n")
                    return

    # Vertices incident to at least one edge must be assigned to exactly one
    # of the two color classes. Isolated vertices can be omitted.
    A = [i + 1 for i in range(n) if adj[i] and color[i] == 0]
    B = [i + 1 for i in range(n) if adj[i] and color[i] == 1]

    # Safety for m == 0 (not necessary under given constraints, but harmless).
    if m == 0:
        A = [1] if n >= 1 else []
        B = [2] if n >= 2 else []

    out = [
        str(len(A)),
        " ".join(map(str, A)),
        str(len(B)),
        " ".join(map(str, B))
    ]
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    solve()