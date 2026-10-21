import sys
from array import array


def solve() -> None:
    data = sys.stdin.buffer.read()
    length = len(data)
    idx = 0

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
    INF = 10**18

    for _ in range(t):
        n = next_int()

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

        a = array('i', [0]) * (n + 1)
        for i in range(1, n + 1):
            a[i] = next_int()

        parent = array('i', [0]) * (n + 1)
        parent[1] = -1

        order = array('i', [0]) * n
        stack = array('i', [0]) * n

        stack[0] = 1
        top = 1
        order_idx = 0

        while top > 0:
            top -= 1
            v = stack[top]

            order[order_idx] = v
            order_idx += 1

            e = head[v]
            pv = parent[v]

            while e != -1:
                w = to[e]
                if w != pv:
                    parent[w] = v
                    stack[top] = w
                    top += 1
                e = nxt[e]

        del head, to, nxt, stack

        leaf_count = array('i', [0]) * (n + 1)
        child_dp_sum = array('q', [0]) * (n + 1)

        answer = 0

        for oi in range(n - 1, -1, -1):
            v = order[oi]

            leaves = leaf_count[v]

            if leaves == 0:
                leaves = 1
                leaf_count[v] = 1
                is_leaf = True
            else:
                is_leaf = False

            if a[v] > 0:
                dp_v = leaves * a[v]
            else:
                dp_v = INF

            if not is_leaf:
                without_v = child_dp_sum[v]
                if without_v < dp_v:
                    dp_v = without_v

            p = parent[v]

            if p > 0:
                leaf_count[p] += leaves

                total = child_dp_sum[p] + dp_v
                if total > INF:
                    total = INF
                child_dp_sum[p] = total
            else:
                answer = dp_v

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()