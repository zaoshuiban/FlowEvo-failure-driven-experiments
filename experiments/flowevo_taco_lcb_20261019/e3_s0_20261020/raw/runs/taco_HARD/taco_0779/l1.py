import sys


def read_ints():
    data = sys.stdin.buffer.read()
    num = 0
    inside = False
    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            inside = True
        else:
            if inside:
                yield num
                num = 0
                inside = False
    if inside:
        yield num


def solve():
    it = read_ints()

    try:
        t = next(it)
    except StopIteration:
        return

    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)

        adj = [[] for _ in range(n + 1)]

        for _ in range(n - 1):
            u = next(it)
            v = next(it)
            adj[u].append(v)
            adj[v].append(u)

        parent = [0] * (n + 1)
        parent[1] = -1

        order = [1]
        idx = 0

        while idx < len(order):
            v = order[idx]
            idx += 1

            for u in adj[v]:
                if u != parent[v]:
                    parent[u] = v
                    order.append(u)

        height = [0] * (n + 1)
        answer = 0

        for v in reversed(order):
            max_child_height = 0

            for u in adj[v]:
                if u != parent[v]:
                    if height[u] > max_child_height:
                        max_child_height = height[u]

            height[v] = max_child_height + 1

            if height[v] <= k:
                answer += 1

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()