import sys
import math


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    data_len = len(data)

    def next_int():
        nonlocal idx
        while idx < data_len and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < data_len and data[idx] > 32:
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

        if n == 1:
            m = next_int()
            output.append(str(m - gcd(m, values[0])))
            continue

        parent = [-1] * n
        path_gcd = [0] * n

        parent[0] = 0
        path_gcd[0] = values[0]

        order = [0]
        ptr = 0

        while ptr < len(order):
            u = order[ptr]
            ptr += 1

            for v in adj[u]:
                if v != parent[u]:
                    parent[v] = u
                    path_gcd[v] = gcd(path_gcd[u], values[v])
                    order.append(v)

        answers = []

        for i in range(n):
            m = next_int()

            if i != 0 and len(adj[i]) == 1:
                answers.append(str(m - gcd(m, path_gcd[i])))

        output.append(" ".join(answers))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()