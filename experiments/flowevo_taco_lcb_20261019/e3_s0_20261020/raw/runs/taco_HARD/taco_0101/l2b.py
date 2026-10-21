import sys
import math


def read_ints():
    data = sys.stdin.buffer.read()
    num = 0
    in_num = False
    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            in_num = True
        else:
            if in_num:
                yield num
                num = 0
                in_num = False
    if in_num:
        yield num


def main():
    it = read_ints()
    try:
        T = next(it)
    except StopIteration:
        return

    gcd = math.gcd
    output_lines = []

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

        ans = [-1] * N
        stack = [(0, -1, 0)]  # node, parent, gcd of values before this node

        while stack:
            u, parent, previous_gcd = stack.pop()

            current_gcd = gcd(previous_gcd, v[u])
            is_leaf = True

            for nxt in adj[u]:
                if nxt != parent:
                    is_leaf = False
                    stack.append((nxt, u, current_gcd))

            if is_leaf:
                d = gcd(current_gcd, m[u])
                ans[u] = m[u] - d

        result = []
        for value in ans:
            if value != -1:
                result.append(str(value))

        output_lines.append(" ".join(result))

    sys.stdout.write("\n".join(output_lines))


if __name__ == "__main__":
    main()