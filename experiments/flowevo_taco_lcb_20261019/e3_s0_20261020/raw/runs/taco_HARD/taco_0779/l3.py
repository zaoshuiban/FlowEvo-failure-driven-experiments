import sys
from array import array


def solve():
    data = sys.stdin.buffer.read()
    if not data:
        return

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
    answers = []

    for _ in range(t):
        n = next_int()
        k = next_int()

        head = array('i', [-1]) * (n + 1)
        m = 2 * (n - 1)
        to = array('i', [0]) * m
        nxt = array('i', [0]) * m

        edge_idx = 0
        for _ in range(n - 1):
            u = next_int()
            v = next_int()

            to[edge_idx] = v
            nxt[edge_idx] = head[u]
            head[u] = edge_idx
            edge_idx += 1

            to[edge_idx] = u
            nxt[edge_idx] = head[v]
            head[v] = edge_idx
            edge_idx += 1

        parent = array('i', [0]) * (n + 1)
        parent[1] = -1

        order = array('i', [0]) * n
        order[0] = 1
        order_size = 1

        stack = [1]

        while stack:
            u = stack.pop()
            e = head[u]
            pu = parent[u]

            while e != -1:
                v = to[e]
                if v != pu:
                    parent[v] = u
                    order[order_size] = v
                    order_size += 1
                    stack.append(v)
                e = nxt[e]

        height = array('i', [1]) * (n + 1)
        answer = 0

        for i in range(n - 1, -1, -1):
            u = order[i]
            hu = height[u]

            if hu <= k:
                answer += 1

            p = parent[u]
            if p > 0:
                candidate = hu + 1
                if candidate > height[p]:
                    height[p] = candidate

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()