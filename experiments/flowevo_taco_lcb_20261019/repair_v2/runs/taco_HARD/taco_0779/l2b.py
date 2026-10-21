import sys


def solve():
    data = sys.stdin.buffer.read()
    data_len = len(data)
    idx = 0

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
    answers = []

    for _ in range(t):
        n = next_int()
        k = next_int()

        adj = [[] for _ in range(n + 1)]
        for _ in range(n - 1):
            u = next_int()
            v = next_int()
            adj[u].append(v)
            adj[v].append(u)

        parent = [0] * (n + 1)
        parent[1] = -1
        order = [1]
        stack = [1]

        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v != parent[u]:
                    parent[v] = u
                    order.append(v)
                    stack.append(v)

        height = [1] * (n + 1)
        answer = 0

        for u in reversed(order):
            if height[u] <= k:
                answer += 1

            p = parent[u]
            if p > 0:
                candidate = height[u] + 1
                if candidate > height[p]:
                    height[p] = candidate

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()