import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    deps = [[] for _ in range(n)]
    for i in range(n):
        c = data[idx]
        idx += 1
        deps[i] = [data[idx + j] - 1 for j in range(c)]
        idx += c

    visited = bytearray(n)
    answer = []

    # state: 0 = enter, 1 = exit
    stack = [(0, 0)]

    while stack:
        v, state = stack.pop()

        if state == 0:
            if visited[v]:
                continue

            visited[v] = 1
            stack.append((v, 1))

            for u in deps[v]:
                if not visited[u]:
                    stack.append((u, 0))
        else:
            if v != 0:
                answer.append(str(v + 1))

    print(" ".join(answer))


if __name__ == "__main__":
    main()