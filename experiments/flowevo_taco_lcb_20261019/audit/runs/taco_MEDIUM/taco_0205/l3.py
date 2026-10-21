import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    a = list(map(int, data[1:1 + n]))

    # order[i] = original index (0-based) of the i-th smallest element
    order = list(range(n))
    order.sort(key=a.__getitem__)

    visited = [False] * n
    cycles = []

    for i in range(n):
        if not visited[i]:
            cycle = []
            cur = i

            while not visited[cur]:
                visited[cur] = True
                cycle.append(cur + 1)  # convert to 1-based index
                cur = order[cur]

            cycles.append(cycle)

    output = [str(len(cycles))]

    for cycle in cycles:
        output.append(str(len(cycle)) + " " + " ".join(map(str, cycle)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()