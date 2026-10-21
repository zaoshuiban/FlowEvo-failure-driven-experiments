import sys


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
    answers = []

    for _ in range(t):
        n = next_int()
        k = next_int()

        if k >= n:
            for _ in range(n - 1):
                next_int()
                next_int()
            answers.append(str(n))
            continue

        adj = [[] for _ in range(n)]

        for _ in range(n - 1):
            u = next_int() - 1
            v = next_int() - 1
            adj[u].append(v)
            adj[v].append(u)

        parent = [-1] * n
        parent[0] = -2
        order = [0]

        pos = 0
        while pos < len(order):
            u = order[pos]
            pos += 1

            for v in adj[u]:
                if v != parent[u]:
                    parent[v] = u
                    order.append(v)

        height = [0] * n

        for i in range(n - 1, 0, -1):
            u = order[i]
            p = parent[u]
            val = height[u] + 1
            if val > height[p]:
                height[p] = val

        ans = 0
        for h in height:
            if h < k:
                ans += 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()