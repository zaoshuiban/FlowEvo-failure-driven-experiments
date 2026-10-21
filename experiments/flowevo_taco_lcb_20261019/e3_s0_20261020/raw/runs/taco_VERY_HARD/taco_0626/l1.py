import sys
from array import array


def int_generator(data):
    num = 0
    in_number = False

    for c in data:
        if c >= 48:  # digit
            num = num * 10 + (c - 48)
            in_number = True
        elif in_number:
            yield num
            num = 0
            in_number = False

    if in_number:
        yield num


def solve():
    data = sys.stdin.buffer.read()
    it = int_generator(data)
    read_int = it.__next__

    t = read_int()
    answers = []
    INF = 10**18

    for _ in range(t):
        n = read_int()

        head = array('i', [-1]) * (n + 1)
        m = 2 * (n - 1)
        to = array('i', [0]) * m
        nxt = array('i', [0]) * m

        edge_idx = 0
        for _ in range(n - 1):
            u = read_int()
            v = read_int()

            to[edge_idx] = v
            nxt[edge_idx] = head[u]
            head[u] = edge_idx
            edge_idx += 1

            to[edge_idx] = u
            nxt[edge_idx] = head[v]
            head[v] = edge_idx
            edge_idx += 1

        values = array('i', [0]) * (n + 1)
        for i in range(1, n + 1):
            values[i] = read_int()

        parent = array('i', [0]) * (n + 1)
        order = array('i')
        stack = array('i', [1])

        while stack:
            u = stack.pop()
            order.append(u)

            e = head[u]
            pu = parent[u]

            while e != -1:
                v = to[e]
                if v != pu:
                    parent[v] = u
                    stack.append(v)
                e = nxt[e]

        del head, to, nxt, stack

        leaf_count = array('i', [0]) * (n + 1)
        dp = array('q', [0]) * (n + 1)

        for i in range(len(order) - 1, -1, -1):
            u = order[i]

            leaves = leaf_count[u]

            if leaves == 0:
                leaves = 1
                leaf_count[u] = 1
                child_sum = INF
            else:
                child_sum = dp[u]

            if values[u] > 0:
                take_u = values[u] * leaves
            else:
                take_u = INF

            if child_sum < take_u:
                best = child_sum
            else:
                best = take_u

            dp[u] = best

            p = parent[u]
            if p != 0:
                leaf_count[p] += leaves

                total = dp[p] + best
                if total > INF:
                    total = INF
                dp[p] = total

        answers.append(str(dp[1]))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()