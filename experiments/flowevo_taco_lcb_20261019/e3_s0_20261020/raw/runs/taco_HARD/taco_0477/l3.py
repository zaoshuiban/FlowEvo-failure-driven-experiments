import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    p = [x - 1 for x in data[1:1 + n]]

    # If p has a fixed vertex, a star centered at it is invariant.
    fixed = -1
    for i in range(n):
        if p[i] == i:
            fixed = i
            break

    if fixed != -1:
        ans = ["YES"]
        for v in range(n):
            if v != fixed:
                ans.append(f"{fixed + 1} {v + 1}")
        sys.stdout.write("\n".join(ans) + "\n")
        return

    # Otherwise, every cycle must have even length, and a 2-cycle is needed
    # as the central edge of the tree.
    visited = [False] * n
    cycles = []
    center = None
    possible = True

    for i in range(n):
        if visited[i]:
            continue

        cur = i
        cycle = []
        while not visited[cur]:
            visited[cur] = True
            cycle.append(cur)
            cur = p[cur]

        cycles.append(cycle)

        if len(cycle) % 2 == 1:
            possible = False
        if len(cycle) == 2 and center is None:
            center = cycle

    if not possible or center is None:
        sys.stdout.write("NO\n")
        return

    a, b = center
    edges = [(a, b)]

    for cycle in cycles:
        if cycle is center:
            continue

        for idx, v in enumerate(cycle):
            if idx % 2 == 0:
                edges.append((a, v))
            else:
                edges.append((b, v))

    ans = ["YES"]
    for u, v in edges:
        ans.append(f"{u + 1} {v + 1}")

    sys.stdout.write("\n".join(ans) + "\n")


if __name__ == "__main__":
    solve()