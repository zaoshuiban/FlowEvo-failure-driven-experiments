import sys

def main():
    input = sys.stdin.buffer.readline

    N, M = map(int, input().split())
    graph = [[] for _ in range(N)]

    for _ in range(M):
        a, b, x, y = map(int, input().split())
        a -= 1
        b -= 1

        graph[a].append((b, x, y))
        graph[b].append((a, -x, -y))

    coordinates = [None] * N
    coordinates[0] = (0, 0)

    stack = [0]

    while stack:
        v = stack.pop()
        vx, vy = coordinates[v]

        for to, dx, dy in graph[v]:
            if coordinates[to] is None:
                coordinates[to] = (vx + dx, vy + dy)
                stack.append(to)

    answer = []
    for coord in coordinates:
        if coord is None:
            answer.append("undecidable")
        else:
            answer.append(f"{coord[0]} {coord[1]}")

    print("\n".join(answer))


if __name__ == "__main__":
    main()