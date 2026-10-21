import sys


def solve():
    data = sys.stdin.buffer.read()
    ndata = len(data)
    idx = 0

    def next_int():
        nonlocal idx
        while idx < ndata and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < ndata and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    T = next_int()
    output = []

    for _ in range(T):
        N = next_int()
        Q = next_int()

        A = [0] * N
        for i in range(N):
            A[i] = next_int()

        M = N - 1
        low = [0] * M
        high = [0] * M

        for i in range(M):
            a = A[i]
            b = A[i + 1]
            if a <= b:
                low[i] = a
                high[i] = b
            else:
                low[i] = b
                high[i] = a

        left_query = [0] * Q
        right_query = [0] * Q
        y_query = [0] * Q

        for qi in range(Q):
            x1 = next_int()
            x2 = next_int()
            y = next_int()

            left_query[qi] = x1
            right_query[qi] = x2 - 1
            y_query[qi] = y

        query_order = list(range(Q))
        query_order.sort(key=y_query.__getitem__)

        answer = [0] * Q
        bit = [0] * (M + 1)

        edge_order = list(range(M))
        edge_order.sort(key=low.__getitem__)

        ptr = 0
        for qi in query_order:
            y = y_query[qi]

            while ptr < M and low[edge_order[ptr]] <= y:
                pos = edge_order[ptr] + 1
                while pos <= M:
                    bit[pos] += 1
                    pos += pos & -pos
                ptr += 1

            l = left_query[qi]
            r = right_query[qi]

            s = 0
            pos = r
            while pos > 0:
                s += bit[pos]
                pos -= pos & -pos

            pos = l - 1
            while pos > 0:
                s -= bit[pos]
                pos -= pos & -pos

            answer[qi] = s

        bit = [0] * (M + 1)

        edge_order = list(range(M))
        edge_order.sort(key=high.__getitem__)

        ptr = 0
        for qi in query_order:
            y = y_query[qi]

            while ptr < M and high[edge_order[ptr]] < y:
                pos = edge_order[ptr] + 1
                while pos <= M:
                    bit[pos] += 1
                    pos += pos & -pos
                ptr += 1

            l = left_query[qi]
            r = right_query[qi]

            s = 0
            pos = r
            while pos > 0:
                s += bit[pos]
                pos -= pos & -pos

            pos = l - 1
            while pos > 0:
                s -= bit[pos]
                pos -= pos & -pos

            answer[qi] -= s

        output.extend(map(str, answer))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()