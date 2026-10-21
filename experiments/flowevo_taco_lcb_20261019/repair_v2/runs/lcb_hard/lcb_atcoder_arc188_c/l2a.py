import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    N = next(it)
    M = next(it)

    # Nodes 0 ... N-1       : x_i, whether villager i is honest
    # Nodes N ... 2N-1      : z_i = x_i xor y_i
    # For testimony A, B, C:
    #   z_A xor x_B = C
    size = 2 * N
    graph = [[] for _ in range(size)]

    for _ in range(M):
        a = next(it) - 1
        b = next(it) - 1
        c = next(it)

        za = N + a
        xb = b

        graph[za].append((xb, c))
        graph[xb].append((za, c))

    value = [-1] * size

    for start in range(size):
        if value[start] != -1:
            continue

        value[start] = 0
        stack = [start]

        while stack:
            u = stack.pop()

            for v, w in graph[u]:
                expected = value[u] ^ w

                if value[v] == -1:
                    value[v] = expected
                    stack.append(v)
                elif value[v] != expected:
                    print(-1)
                    return

    ans = []
    for i in range(N):
        x_i = value[i]
        z_i = value[N + i]
        y_i = x_i ^ z_i
        ans.append(str(y_i))

    print("".join(ans))


if __name__ == "__main__":
    main()