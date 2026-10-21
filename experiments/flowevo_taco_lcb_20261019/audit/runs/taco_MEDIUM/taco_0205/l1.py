import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    sorted_positions = sorted(range(n), key=lambda i: a[i])

    p = [0] * n
    for rank, pos in enumerate(sorted_positions, start=1):
        p[pos] = rank

    visited = [False] * n
    cycles = []

    for i in range(n):
        if not visited[i]:
            cycle = []
            cur = i
            while not visited[cur]:
                visited[cur] = True
                cycle.append(cur + 1)
                cur = p[cur] - 1
            cycles.append(cycle)

    out = [str(len(cycles))]
    for cycle in cycles:
        out.append(str(len(cycle)) + " " + " ".join(map(str, cycle)))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()