import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    n = data[idx]
    idx += 1

    prerequisites = [[] for _ in range(n)]
    for i in range(n):
        c = data[idx]
        idx += 1
        prerequisites[i] = [data[idx + j] - 1 for j in range(c)]
        idx += c

    visited = [False] * n
    ans = []

    # (state, node)
    # state 0: enter node
    # state 1: exit node after processing prerequisites
    stack = [(0, 0)]

    while stack:
        state, u = stack.pop()

        if state == 0:
            if visited[u]:
                continue
            visited[u] = True

            stack.append((1, u))

            for v in prerequisites[u]:
                if not visited[v]:
                    stack.append((0, v))
        else:
            if u != 0:
                ans.append(u + 1)

    print(*ans)


if __name__ == "__main__":
    main()