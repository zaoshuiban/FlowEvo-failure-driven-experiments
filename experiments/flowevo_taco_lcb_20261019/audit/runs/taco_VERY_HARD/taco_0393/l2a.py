import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    T = next(it)
    output = []

    for _ in range(T):
        N = next(it)
        Q = next(it)

        A = [next(it) for _ in range(N)]

        m = N - 1
        L = [0] * m
        R = [0] * m

        for i in range(m):
            a = A[i]
            b = A[i + 1]
            if a < b:
                L[i] = a
                R[i] = b
            else:
                L[i] = b
                R[i] = a

        queries = []
        for qi in range(Q):
            x1 = next(it)
            x2 = next(it)
            y = next(it)

            # Segment indices are 0-based: segment i corresponds to i+1 in 1-based.
            # We need segments from x1 to x2-1 in 1-based, i.e. x1-1 to x2-2 in 0-based.
            l = x1 - 1
            r = x2 - 2
            queries.append((y, l, r, qi))

        ans = [0] * Q
        sorted_queries = sorted(queries, key=lambda q: q[0])

        # Count intervals with L_i <= y
        order = sorted(range(m), key=L.__getitem__)
        bit = [0] * (m + 2)
        p = 0

        for y, l, r, qi in sorted_queries:
            while p < m and L[order[p]] <= y:
                idx = order[p] + 1
                while idx <= m:
                    bit[idx] += 1
                    idx += idx & -idx
                p += 1

            s = 0
            idx = r + 1
            while idx > 0:
                s += bit[idx]
                idx -= idx & -idx

            if l > 0:
                idx = l
                while idx > 0:
                    s -= bit[idx]
                    idx -= idx & -idx

            ans[qi] += s

        # Subtract intervals with R_i < y
        order = sorted(range(m), key=R.__getitem__)
        bit = [0] * (m + 2)
        p = 0

        for y, l, r, qi in sorted_queries:
            while p < m and R[order[p]] < y:
                idx = order[p] + 1
                while idx <= m:
                    bit[idx] += 1
                    idx += idx & -idx
                p += 1

            s = 0
            idx = r + 1
            while idx > 0:
                s += bit[idx]
                idx -= idx & -idx

            if l > 0:
                idx = l
                while idx > 0:
                    s -= bit[idx]
                    idx -= idx & -idx

            ans[qi] -= s

        output.extend(map(str, ans))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()