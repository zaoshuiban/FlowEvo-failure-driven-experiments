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
        N = next(it)

        adj = [[] for _ in range(N)]
        for _ in range(N - 1):
            x = next(it) - 1
            y = next(it) - 1
            adj[x].append(y)
            adj[y].append(x)

        v = [next(it) for _ in range(N)]
        m = [next(it) for _ in range(N)]

        parent = [-1] * N
        parent[0] = -2

        path_gcd = [0] * N
        path_gcd[0] = v[0]

        child_count = [0] * N
        order = [0]
        idx = 0

        while idx < len(order):
            u = order[idx]
            idx += 1

            for nxt in adj[u]:
                if nxt == parent[u]:
                    continue

                parent[nxt] = u
                child_count[u] += 1
                path_gcd[nxt] = gcd(path_gcd[u], v[nxt])
                order.append(nxt)

        answers = []
        for u in range(N):
            if child_count[u] == 0:  # leaf in the rooted tree
                g = gcd(path_gcd[u], m[u])
                answers.append(str(m[u] - g))

        output.append(" ".join(answers))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()