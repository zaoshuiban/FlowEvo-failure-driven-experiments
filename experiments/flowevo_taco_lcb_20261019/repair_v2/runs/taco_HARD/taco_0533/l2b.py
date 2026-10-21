import sys


def solve() -> None:
    data = iter(map(int, sys.stdin.buffer.read().split()))
    try:
        n = next(data)
    except StopIteration:
        return
    m = next(data)

    forbidden = [[] for _ in range(n)]

    for _ in range(m):
        x = next(data) - 1
        y = next(data) - 1
        forbidden[x].append(y)
        forbidden[y].append(x)

    unvisited = set(range(n))
    mark = [0] * n
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

            token = v + 1
            for u in forbidden[v]:
                mark[u] = token

            to_add = []
            for u in unvisited:
                if mark[u] != token:
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