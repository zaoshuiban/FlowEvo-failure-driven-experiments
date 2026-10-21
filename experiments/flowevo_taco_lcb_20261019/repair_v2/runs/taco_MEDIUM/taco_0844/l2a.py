import sys


def solve():
    data = sys.stdin.buffer.read()
    if not data:
        return

    def int_generator():
        num = 0
        inside = False
        for c in data:
            if 48 <= c <= 57:
                num = num * 10 + (c - 48)
                inside = True
            elif inside:
                yield num
                num = 0
                inside = False
        if inside:
            yield num

    it = int_generator()

    n = next(it)

    graph = [[] for _ in range(n + 1)]
    for _ in range(n - 1):
        a = next(it)
        b = next(it)
        graph[a].append(b)
        graph[b].append(a)

    tin = [0] * (n + 1)
    tout = [0] * (n + 1)
    parent = [0] * (n + 1)

    timer = 0
    stack = [(1, 0)]  # (node, state), state 0 = enter, 1 = exit

    while stack:
        node, state = stack.pop()

        if state == 0:
            tin[node] = timer
            timer += 1

            stack.append((node, 1))

            for nxt in graph[node]:
                if nxt != parent[node]:
                    parent[nxt] = node
                    stack.append((nxt, 0))
        else:
            tout[node] = timer

    q = next(it)
    answers = []

    for _ in range(q):
        query_type = next(it)
        x = next(it)
        y = next(it)

        if query_type == 0:
            # Bob moves towards root: Oliver x must be an ancestor of y.
            if tin[x] <= tin[y] < tout[x]:
                answers.append("YES")
            else:
                answers.append("NO")
        else:
            # Bob moves away from root: Oliver x must be in subtree of y.
            if tin[y] <= tin[x] < tout[y]:
                answers.append("YES")
            else:
                answers.append("NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()