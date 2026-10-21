import sys
from math import gcd


def read_ints():
    data = sys.stdin.buffer.read()
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


def main():
    it = iter(read_ints())

    try:
        T = next(it)
    except StopIteration:
        return

    output = []

    for _ in range(T):
        n = next(it)

        adj = [[] for _ in range(n)]
        for _ in range(n - 1):
            x = next(it) - 1
            y = next(it) - 1
            adj[x].append(y)
            adj[y].append(x)

        v = [next(it) for _ in range(n)]
        m = [next(it) for _ in range(n)]

        if n == 1:
            g = gcd(v[0], m[0])
            output.append(str(m[0] - g))
            continue

        parent = [-1] * n
        parent[0] = 0

        path_gcd = [0] * n
        path_gcd[0] = v[0]

        stack = [0]

        while stack:
            u = stack.pop()

            for w in adj[u]:
                if parent[w] != -1:
                    continue

                parent[w] = u
                path_gcd[w] = gcd(path_gcd[u], v[w])
                stack.append(w)

        answers = []

        for u in range(n):
            # In a rooted tree with n >= 2, a non-root node is a leaf
            # iff it has degree 1.
            if u != 0 and len(adj[u]) == 1:
                g = gcd(path_gcd[u], m[u])
                answers.append(str(m[u] - g))

        output.append(" ".join(answers))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()