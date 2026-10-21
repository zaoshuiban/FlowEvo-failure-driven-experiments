import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    adj = [[] for _ in range(n + 1)]
    for _ in range(n - 1):
        a = data[idx]
        b = data[idx + 1]
        idx += 2
        adj[a].append(b)
        adj[b].append(a)

    tin = [0] * (n + 1)
    tout = [0] * (n + 1)

    timer = 0
    stack = [(1, 0, 0)]  # node, parent, state: 0 = enter, 1 = exit

    while stack:
        node, parent, state = stack.pop()

        if state == 0:
            timer += 1
            tin[node] = timer
            stack.append((node, parent, 1))

            for nxt in adj[node]:
                if nxt != parent:
                    stack.append((nxt, node, 0))
        else:
            tout[node] = timer

    q = data[idx]
    idx += 1

    answers = []
    append = answers.append

    for _ in range(q):
        query_type = data[idx]
        x = data[idx + 1]
        y = data[idx + 2]
        idx += 3

        if query_type == 0:
            # Bob moves towards root: X must be an ancestor of Y.
            if tin[x] <= tin[y] <= tout[x]:
                append("YES")
            else:
                append("NO")
        else:
            # Bob moves away from root: X must be in the subtree of Y.
            if tin[y] <= tin[x] <= tout[y]:
                append("YES")
            else:
                append("NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()