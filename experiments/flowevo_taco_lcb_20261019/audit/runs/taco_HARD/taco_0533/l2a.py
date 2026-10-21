import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    bad = [None] * n

    idx = 2
    for _ in range(m):
        x = data[idx] - 1
        y = data[idx + 1] - 1
        idx += 2

        if bad[x] is None:
            bad[x] = set()
        bad[x].add(y)

        if bad[y] is None:
            bad[y] = set()
        bad[y].add(x)

    unvisited = set(range(n))
    component_sizes = []

    for start in range(n):
        if start not in unvisited:
            continue

        unvisited.remove(start)
        queue = [start]
        head = 0

        while head < len(queue):
            v = queue[head]
            head += 1

            if not unvisited:
                break

            forbidden = bad[v]

            if forbidden is None:
                queue.extend(unvisited)
                unvisited.clear()
                break

            removed = []
            for u in unvisited:
                if u not in forbidden:
                    removed.append(u)

            if removed:
                for u in removed:
                    unvisited.remove(u)
                queue.extend(removed)

        component_sizes.append(len(queue))

    component_sizes.sort()

    output = [
        str(len(component_sizes)),
        " ".join(map(str, component_sizes))
    ]
    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()