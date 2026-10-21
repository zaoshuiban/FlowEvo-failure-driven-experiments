import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    a = list(map(int, data[1:1 + n]))

    sorted_a = sorted(a)
    rank = {value: i for i, value in enumerate(sorted_a)}  # 0-based target positions

    # p[i] is the target position of a[i] in the fully sorted sequence
    p = [rank[value] for value in a]

    visited = [False] * n
    cycles = []

    for i in range(n):
        if not visited[i]:
            cycle = []
            cur = i
            while not visited[cur]:
                visited[cur] = True
                cycle.append(cur + 1)  # convert to 1-based index
                cur = p[cur]
            cycles.append(cycle)

    result = [str(len(cycles))]
    for cycle in cycles:
        result.append(str(len(cycle)) + " " + " ".join(map(str, cycle)))

    sys.stdout.write("\n".join(result))


if __name__ == "__main__":
    solve()