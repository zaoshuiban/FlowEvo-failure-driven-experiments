import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    m = next(it)

    cats = [0] + [next(it) for _ in range(n)]

    graph = [[] for _ in range(n + 1)]

    for _ in range(n - 1):
        x = next(it)
        y = next(it)
        graph[x].append(y)
        graph[y].append(x)

    answer = 0

    stack = [(1, 0, cats[1])]

    while stack:
        node, parent, consecutive_cats = stack.pop()

        if consecutive_cats > m:
            continue

        if node != 1 and len(graph[node]) == 1:
            answer += 1
            continue

        for neighbor in graph[node]:
            if neighbor == parent:
                continue

            if cats[neighbor] == 1:
                next_consecutive = consecutive_cats + 1
            else:
                next_consecutive = 0

            stack.append((neighbor, node, next_consecutive))

    print(answer)


if __name__ == "__main__":
    main()