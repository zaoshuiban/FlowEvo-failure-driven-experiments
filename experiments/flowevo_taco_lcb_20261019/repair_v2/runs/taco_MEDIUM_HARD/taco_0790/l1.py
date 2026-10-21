import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = [0] + data[1:1 + n]

    state = [0] * (n + 1)
    position = [0] * (n + 1)
    cycles = []

    # Find one representative vertex from every directed cycle.
    for start in range(1, n + 1):
        if state[start] != 0:
            continue

        path = []
        u = start

        while state[u] == 0:
            state[u] = 1
            position[u] = len(path)
            path.append(u)
            u = a[u]

        if state[u] == 1:
            cycle_start = position[u]
            cycles.append(path[cycle_start])

        for v in path:
            state[v] = 2

    root = -1
    for i in range(1, n + 1):
        if a[i] == i:
            root = i
            break

    changes = 0

    if root == -1:
        root = cycles[0]
        a[root] = root
        changes = 1

        for v in cycles[1:]:
            a[v] = root
            changes += 1
    else:
        for v in cycles:
            if v != root:
                a[v] = root
                changes += 1

    print(changes)
    print(*a[1:])


if __name__ == "__main__":
    solve()