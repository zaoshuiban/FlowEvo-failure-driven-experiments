import sys

MOD = 10**9 + 7

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    knowledge = data[2:2 + n]

    adj = [[] for _ in range(n)]
    idx = 2 + n

    for _ in range(m):
        u = data[idx] - 1
        v = data[idx + 1] - 1
        idx += 2

        adj[u].append(v)
        adj[v].append(u)

    visited = [False] * n
    answer = 1

    for start in range(n):
        if visited[start]:
            continue

        visited[start] = True
        stack = [start]

        max_knowledge = -1
        count_max = 0

        while stack:
            u = stack.pop()
            value = knowledge[u]

            if value > max_knowledge:
                max_knowledge = value
                count_max = 1
            elif value == max_knowledge:
                count_max += 1

            for v in adj[u]:
                if not visited[v]:
                    visited[v] = True
                    stack.append(v)

        answer = (answer * count_max) % MOD

    print(answer)


if __name__ == "__main__":
    solve()