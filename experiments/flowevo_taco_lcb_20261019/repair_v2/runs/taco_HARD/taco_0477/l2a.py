import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    p = [x - 1 for x in data[1:1 + n]]

    visited = [False] * n
    cycles = []
    fixed = -1

    for start in range(n):
        if visited[start]:
            continue

        cycle = []
        v = start
        while not visited[v]:
            visited[v] = True
            cycle.append(v)
            v = p[v]

        cycles.append(cycle)
        if len(cycle) == 1 and fixed == -1:
            fixed = cycle[0]

    # If there is a fixed vertex, a star centered at it works.
    if fixed != -1:
        ans = ["YES"]
        for v in range(n):
            if v != fixed:
                ans.append(f"{fixed + 1} {v + 1}")
        sys.stdout.write("\n".join(ans))
        return

    # Without fixed vertices, the tree center must be an edge,
    # whose endpoints form a 2-cycle. Every cycle must be even.
    center_index = -1
    for i, cycle in enumerate(cycles):
        if len(cycle) == 2 and center_index == -1:
            center_index = i

    if center_index == -1:
        sys.stdout.write("NO")
        return

    for cycle in cycles:
        if len(cycle) % 2 != 0:
            sys.stdout.write("NO")
            return

    c1, c2 = cycles[center_index]

    ans = ["YES", f"{c1 + 1} {c2 + 1}"]

    for i, cycle in enumerate(cycles):
        if i == center_index:
            continue

        for pos, v in enumerate(cycle):
            if pos % 2 == 0:
                ans.append(f"{c1 + 1} {v + 1}")
            else:
                ans.append(f"{c2 + 1} {v + 1}")

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    main()