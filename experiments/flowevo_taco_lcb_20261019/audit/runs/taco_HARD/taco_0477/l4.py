import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    p = [x - 1 for x in data[1:1 + n]]

    # If p has a fixed vertex, a star centered at it is invariant.
    for center in range(n):
        if p[center] == center:
            ans = ["YES"]
            for v in range(n):
                if v != center:
                    ans.append(f"{center + 1} {v + 1}")
            sys.stdout.write("\n".join(ans) + "\n")
            return

    # Otherwise, every cycle must have even length, and a 2-cycle
    # is needed for the central edge of the tree.
    visited = [False] * n
    cycles = []
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

    if not possible:
        sys.stdout.write("NO\n")
        return

    center_idx = -1
    for idx, cycle in enumerate(cycles):
        if len(cycle) == 2:
            center_idx = idx
            break

    if center_idx == -1:
        sys.stdout.write("NO\n")
        return

    a, b = cycles[center_idx]
    edges = [(a, b)]

    for idx, cycle in enumerate(cycles):
        if idx == center_idx:
            continue

        for pos, v in enumerate(cycle):
            if pos % 2 == 0:
                edges.append((a, v))
            else:
                edges.append((b, v))

    ans = ["YES"]
    for u, v in edges:
        ans.append(f"{u + 1} {v + 1}")

    sys.stdout.write("\n".join(ans) + "\n")


if __name__ == "__main__":
    solve()