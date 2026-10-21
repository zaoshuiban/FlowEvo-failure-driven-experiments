import sys
from array import array


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    L = len(data)

    def next_int():
        nonlocal idx
        while idx < L and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < L and data[idx] > 32:
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

        A = array('i', [0]) * (n + 1)
        for i in range(1, n + 1):
            A[i] = next_int()

        parent = array('i', [0]) * (n + 1)
        parent[1] = -1

        order = array('i', [0]) * n
        order[0] = 1

        tail = 1
        pos = 0

        while pos < tail:
            u = order[pos]
            pos += 1

            e = head[u]
            p = parent[u]

            while e != -1:
                v = to[e]
                if v != p:
                    parent[v] = u
                    order[tail] = v
                    tail += 1
                e = nxt[e]

        leaf_count = array('i', [0]) * (n + 1)
        dp = array('q', [0]) * (n + 1)

        for pos in range(n - 1, -1, -1):
            u = order[pos]
            e = head[u]

            leaves = 0
            children_sum = 0
            has_child = False

            while e != -1:
                v = to[e]
                if parent[v] == u:
                    has_child = True
                    leaves += leaf_count[v]
                    children_sum += dp[v]
                    if children_sum > INF:
                        children_sum = INF
                e = nxt[e]

            if not has_child:
                leaf_count[u] = 1
                if A[u] > 0:
                    dp[u] = A[u]
                else:
                    dp[u] = INF
            else:
                leaf_count[u] = leaves

                if A[u] > 0:
                    take_u = A[u] * leaves
                else:
                    take_u = INF

                not_take_u = children_sum
                dp[u] = take_u if take_u < not_take_u else not_take_u

        answers.append(str(dp[1]))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()