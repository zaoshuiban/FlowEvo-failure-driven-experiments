import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)

    graph = [[] for _ in range(n)]
    for _ in range(n - 1):
        u = next(it) - 1
        v = next(it) - 1
        graph[u].append(v)
        graph[v].append(u)

    degree = [len(neighbors) for neighbors in graph]

    visited = [False] * n
    answer = 0

    for start in range(n):
        if degree[start] != 3 or visited[start]:
            continue

        visited[start] = True
        stack = [start]
        count_degree_two = 0

        while stack:
            v = stack.pop()

            for nxt in graph[v]:
                if degree[nxt] == 2:
                    count_degree_two += 1
                elif degree[nxt] == 3 and not visited[nxt]:
                    visited[nxt] = True
                    stack.append(nxt)

        answer += count_degree_two * (count_degree_two - 1) // 2

    print(answer)


if __name__ == "__main__":
    main()