import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    forbidden = [None] * (n + 1)

    pos = 2
    for _ in range(m):
        x = data[pos]
        y = data[pos + 1]
        pos += 2

        s = forbidden[x]
        if s is None:
            s = set()
            forbidden[x] = s
        s.add(y)

        s = forbidden[y]
        if s is None:
            s = set()
            forbidden[y] = s
        s.add(x)

    del data

    unvisited = set(range(1, n + 1))
    components = []

    while unvisited:
        start = unvisited.pop()
        queue = [start]
        head = 0

        while head < len(queue):
            v = queue[head]
            head += 1

            if not unvisited:
                break

            forbidden_v = forbidden[v]

            if forbidden_v is None:
                queue.extend(unvisited)
                unvisited.clear()
                break

            for u in list(unvisited):
                if u not in forbidden_v:
                    unvisited.remove(u)
                    queue.append(u)

        components.append(len(queue))

    components.sort()

    sys.stdout.write(str(len(components)) + "\n")
    sys.stdout.write(" ".join(map(str, components)) + "\n")


if __name__ == "__main__":
    solve()