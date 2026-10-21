import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    a = list(map(int, data[1:1 + n]))

    # order[rank] = original position (0-based) of the element with this rank
    order = sorted(range(n), key=a.__getitem__)

    # p[position] = rank/target position of the element at this position
    p = [0] * n
    for rank, pos in enumerate(order):
        p[pos] = rank

    visited = [False] * n
    cycles = []

    for start in range(n):
        if visited[start]:
            continue

        cycle = []
        cur = start

        while not visited[cur]:
            visited[cur] = True
            cycle.append(cur + 1)  # convert to 1-based index
            cur = p[cur]

        cycle.sort()
        cycles.append(cycle)

    cycles.sort(key=lambda c: c[0])

    output = [str(len(cycles))]
    for cycle in cycles:
        output.append(str(len(cycle)) + " " + " ".join(map(str, cycle)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()