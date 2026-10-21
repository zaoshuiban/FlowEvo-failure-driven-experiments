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

        answer = 0

        for oi in range(n - 1, -1, -1):
            u = order[oi]
            leaves = leaf_count[u]
            au = A[u]

            if leaves == 0:
                lc = 1
                if au > 0:
                    val = au
                else:
                    val = INF
            else:
                lc = leaves

                if au > 0:
                    take = au * leaves
                    not_take = dp[u]
                    if not_take > INF:
                        not_take = INF
                    val = take if take < not_take else not_take
                else:
                    val = dp[u]
                    if val > INF:
                        val = INF

            dp[u] = val

            p = parent[u]
            if p != -1:
                leaf_count[p] += lc
                s = dp[p] + val
                if s > INF:
                    s = INF
                dp[p] = s
            else:
                answer = val

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()