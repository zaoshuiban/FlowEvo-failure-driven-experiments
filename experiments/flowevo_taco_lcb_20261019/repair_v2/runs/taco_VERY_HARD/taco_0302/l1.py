import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    adj = [[] for _ in range(n)]
    masks = [0] * n

    for _ in range(m):
        a = next(it) - 1
        b = next(it) - 1
        adj[a].append(b)
        adj[b].append(a)
        masks[a] |= 1 << b
        masks[b] |= 1 << a

    color = [-1] * n
    components = []

    for start in range(n):
        if color[start] != -1:
            continue

        color[start] = 0
        queue = [start]
        head = 0
        vertices = []

        while head < len(queue):
            v = queue[head]
            head += 1
            vertices.append(v)

            for u in adj[v]:
                if color[u] == -1:
                    color[u] = color[v] ^ 1
                    queue.append(u)
                elif color[u] == color[v]:
                    print(-1)
                    return

        components.append(vertices)

    answer = 0

    for vertices in components:
        size = len(vertices)
        if size == 1:
            continue

        diameter = 0

        for source in vertices:
            visited = 1 << source
            frontier = visited
            distance = 0

            while True:
                neighbours = 0
                f = frontier

                while f:
                    lsb = f & -f
                    vertex = lsb.bit_length() - 1
                    neighbours |= masks[vertex]
                    f ^= lsb

                neighbours &= ~visited
                if neighbours == 0:
                    break

                visited |= neighbours
                frontier = neighbours
                distance += 1

            if distance > diameter:
                diameter = distance
                if diameter == size - 1:
                    break

        answer += diameter

    print(answer)


if __name__ == "__main__":
    main()