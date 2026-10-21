import sys


def solve():
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    n = int(next(it))

    adj = [[] for _ in range(n + 1)]
    for _ in range(n - 1):
        a = int(next(it))
        b = int(next(it))
        adj[a].append(b)
        adj[b].append(a)

    tin = [0] * (n + 1)
    tout = [0] * (n + 1)

    timer = 0
    stack = [(1, 0, 0)]  # node, parent, state: 0 enter, 1 exit

    while stack:
        node, parent, state = stack.pop()

        if state == 0:
            timer += 1
            tin[node] = timer
            stack.append((node, parent, 1))

            for child in adj[node]:
                if child != parent:
                    stack.append((child, node, 0))
        else:
            tout[node] = timer

    q = int(next(it))
    answers = []

    for _ in range(q):
        typ = int(next(it))
        x = int(next(it))
        y = int(next(it))

        if typ == 0:
            # Bob moves towards the root.
            # Oliver at x is found if x is an ancestor of y.
            if tin[x] <= tin[y] <= tout[x]:
                answers.append("YES")
            else:
                answers.append("NO")
        else:
            # Bob moves away from the root.
            # Oliver at x is found if x is in the subtree of y.
            if tin[y] <= tin[x] <= tout[y]:
                answers.append("YES")
            else:
                answers.append("NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()