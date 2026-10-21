import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    perm = data[1:1 + n]

    p = [0] * (n + 1)
    for i, v in enumerate(perm, 1):
        p[i] = v

    # If there is a fixed point, a star centered at it always works.
    for i in range(1, n + 1):
        if p[i] == i:
            out = ["YES"]
            for j in range(1, n + 1):
                if j != i:
                    out.append(f"{i} {j}")
            sys.stdout.write("\n".join(out))
            return

    # No fixed point: all cycles must be even, and there must be a 2-cycle.
    visited = [False] * (n + 1)
    cycles = []
    center_idx = -1
    all_even = True

    for i in range(1, n + 1):
        if not visited[i]:
            cycle = []
            cur = i
            while not visited[cur]:
                visited[cur] = True
                cycle.append(cur)
                cur = p[cur]

            if len(cycle) % 2 == 1:
                all_even = False

            if len(cycle) == 2 and center_idx == -1:
                center_idx = len(cycles)

            cycles.append(cycle)

    if not all_even or center_idx == -1:
        sys.stdout.write("NO")
        return

    a, b = cycles[center_idx]

    out = ["YES", f"{a} {b}"]

    for idx, cycle in enumerate(cycles):
        if idx == center_idx:
            continue

        c = cycle[0]
        cur_center = a
        length = len(cycle)

        for _ in range(length):
            out.append(f"{cur_center} {c}")
            cur_center = b if cur_center == a else a
            c = p[c]

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()