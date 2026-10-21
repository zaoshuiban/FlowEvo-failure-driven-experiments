import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    forbidden = [[] for _ in range(n)]

    idx = 2
    for _ in range(m):
        x = data[idx] - 1
        y = data[idx + 1] - 1
        idx += 2
        forbidden[x].append(y)
        forbidden[y].append(x)

    unvisited = set(range(n))
    mark = [0] * n
    stamp = 0
    components = []

    while unvisited:
        start = unvisited.pop()
        queue = [start]
        head = 0
        size = 0

        while head < len(queue):
            v = queue[head]
            head += 1
            size += 1

            stamp += 1
            for u in forbidden[v]:
                mark[u] = stamp

            to_add = []
            for u in unvisited:
                if mark[u] != stamp:
                    to_add.append(u)

            if to_add:
                unvisited.difference_update(to_add)
                queue.extend(to_add)

        components.append(size)

    components.sort()

    sys.stdout.write(str(len(components)) + "\n")
    sys.stdout.write(" ".join(map(str, components)) + "\n")


if __name__ == "__main__":
    solve()