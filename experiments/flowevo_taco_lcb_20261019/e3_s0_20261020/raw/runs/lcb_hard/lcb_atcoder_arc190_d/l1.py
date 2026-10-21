import sys


def mat_mul(A, B, mod):
    n = len(A)
    C = [[0] * n for _ in range(n)]

    for i in range(n):
        Ci = C[i]
        Ai = A[i]

        for k in range(n):
            aik = Ai[k]
            if aik:
                Bk = B[k]
                for j in range(n):
                    Ci[j] += aik * Bk[j]

        for j in range(n):
            Ci[j] %= mod

    return C


def mat_pow(A, exp, mod):
    n = len(A)
    res = None
    base = A
    e = exp

    while e:
        if e & 1:
            if res is None:
                res = [row[:] for row in base]
            else:
                res = mat_mul(res, base, mod)

        e >>= 1
        if e:
            base = mat_mul(base, base, mod)

    if res is None:
        res = [[0] * n for _ in range(n)]
        for i in range(n):
            res[i][i] = 1 % mod

    return res


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    p = next(it)

    A = [[next(it) for _ in range(n)] for _ in range(n)]

    zeros = []
    for i in range(n):
        for j in range(n):
            if A[i][j] == 0:
                zeros.append((i, j))

    K = len(zeros)

    if p == 1:
        line = " ".join(["0"] * n)
        sys.stdout.write("\n".join([line] * n))
        return

    # For p = 2, every zero is replaced by 1, so B is the all-one matrix.
    if p == 2:
        val = n & 1
        line = " ".join([str(val)] * n)
        sys.stdout.write("\n".join([line] * n))
        return

    C = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if A[i][j] != 0:
                C[i][j] = A[i][j] % p

    base = mat_pow(C, p, p)
    ans = [row[:] for row in base]

    for u, v in zeros:
        if u == v:
            # C * E_{u,u}
            for i in range(n):
                val = ans[i][u] + C[i][u]
                if val >= p:
                    val -= p
                ans[i][u] = val

            # E_{u,u} * C
            for j in range(n):
                val = ans[u][j] + C[u][j]
                if val >= p:
                    val -= p
                ans[u][j] = val

            # (p - 2) * C_{u,u} * E_{u,u}
            coef = ((p - 2) % p) * C[u][u] % p
            if coef:
                val = ans[u][u] + coef
                if val >= p:
                    val -= p
                ans[u][u] = val

        else:
            # Only p = 3 has an additional contribution for off-diagonal zero entries.
            if p == 3:
                add = C[v][u]
                if add:
                    val = ans[u][v] + add
                    if val >= p:
                        val -= p
                    ans[u][v] = val

    if K & 1:
        for i in range(n):
            row = ans[i]
            for j in range(n):
                if row[j]:
                    row[j] = p - row[j]

    out = [" ".join(map(str, row)) for row in ans]
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()