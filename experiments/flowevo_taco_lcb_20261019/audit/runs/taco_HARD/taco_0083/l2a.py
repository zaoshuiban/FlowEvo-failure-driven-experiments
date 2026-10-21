import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)

    adj = [[] for _ in range(n)]

    for _ in range(m):
        a = next(it) - 1
        b = next(it) - 1
        c = next(it)

        # We need: c XOR x[a] XOR x[b] = 1
        # Therefore: x[a] XOR x[b] = 1 XOR c
        need = 1 ^ c

        adj[a].append((b, need))
        adj[b].append((a, need))

    value = [-1] * n

    for start in range(n):
        if value[start] != -1:
            continue

        value[start] = 0
        stack = [start]

        while stack:
            u = stack.pop()

            for v, need in adj[u]:
                expected = value[u] ^ need

                if value[v] == -1:
                    value[v] = expected
                    stack.append(v)
                elif value[v] != expected:
                    print("Impossible")
                    return

    answer = [str(i + 1) for i in range(n) if value[i] == 1]

    print(len(answer))
    print(" ".join(answer))


if __name__ == "__main__":
    main()