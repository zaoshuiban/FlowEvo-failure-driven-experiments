import sys
import math


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    output = []
    gcd = math.gcd

    for _ in range(t):
        n = next_int()

        adj = [[] for _ in range(n)]
        for _ in range(n - 1):
            x = next_int() - 1
            y = next_int() - 1
            adj[x].append(y)
            adj[y].append(x)

        values = [0] * n
        for i in range(n):
            values[i] = next_int()

        mods = [0] * n
        for i in range(n):
            mods[i] = next_int()

        parent = [-1] * n
        path_gcd = [0] * n
        is_leaf = bytearray(n)

        path_gcd[0] = values[0]
        stack = [0]

        while stack:
            u = stack.pop()
            child_count = 0
            current_gcd = path_gcd[u]
            parent_u = parent[u]

            for v in adj[u]:
                if v == parent_u:
                    continue

                parent[v] = u
                path_gcd[v] = gcd(current_gcd, values[v])
                stack.append(v)
                child_count += 1

            if child_count == 0:
                is_leaf[u] = 1

        answers = []
        for i in range(n):
            if is_leaf[i]:
                d = gcd(path_gcd[i], mods[i])
                answers.append(str(mods[i] - d))

        output.append(" ".join(answers))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()