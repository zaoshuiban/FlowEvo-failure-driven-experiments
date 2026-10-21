import sys
from array import array


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
        child_sum = array('q', [0]) * (n + 1)

        answer = 0

        for i in range(n - 1, -1, -1):
            u = order[i]

            leaves = leaf_count[u]

            if leaves == 0:
                leaves = 1
                best_without_u = INF
            else:
                best_without_u = child_sum[u]

            if A[u] > 0:
                best_with_u = A[u] * leaves
            else:
                best_with_u = INF

            best = best_with_u if best_with_u < best_without_u else best_without_u

            p = parent[u]
            if p != 0:
                leaf_count[p] += leaves
                s = child_sum[p] + best
                if s > INF:
                    s = INF
                child_sum[p] = s
            else:
                answer = best

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()