import sys


def int_stream():
    data = sys.stdin.buffer.read()
    num = 0
    in_number = False

    for c in data:
        if c > 32:
            num = num * 10 + (c - 48)
            in_number = True
        elif in_number:
            yield num
            num = 0
            in_number = False

    if in_number:
        yield num


def solve():
    it = iter(int_stream())

    try:
        n = next(it)
    except StopIteration:
        return

    adj = [[] for _ in range(n + 1)]

    for _ in range(n - 1):
        a = next(it)
        b = next(it)
        adj[a].append(b)
        adj[b].append(a)

    tin = [0] * (n + 1)
    tout = [0] * (n + 1)

    timer = 0
    stack = [(1, 0, 0)]  # node, parent, state (0 = enter, 1 = exit)

    while stack:
        u, parent, state = stack.pop()

        if state == 0:
            timer += 1
            tin[u] = timer

            stack.append((u, parent, 1))

            for v in adj[u]:
                if v != parent:
                    stack.append((v, u, 0))
        else:
            tout[u] = timer

    q = next(it)
    answers = []
    append = answers.append

    for _ in range(q):
        query_type = next(it)
        x = next(it)
        y = next(it)

        if query_type == 0:
            # Bob moves from y towards root 1.
            # Oliver at x is found iff x is an ancestor of y.
            if tin[x] <= tin[y] <= tout[x]:
                append("YES\n")
            else:
                append("NO\n")
        else:
            # Bob moves from y away from root 1.
            # Oliver at x is found iff x is in y's subtree.
            if tin[y] <= tin[x] <= tout[y]:
                append("YES\n")
            else:
                append("NO\n")

    sys.stdout.write("".join(answers))


if __name__ == "__main__":
    solve()