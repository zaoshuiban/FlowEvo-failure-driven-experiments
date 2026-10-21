import sys

MOD = 10**9 + 7


def mat_mul(A, B):
    n = len(A)
    C = [[0] * n for _ in range(n)]

    for i in range(n):
        Ci = C[i]
        Ai = A[i]

        for k in range(n):
            a = Ai[k]
            if a:
                Bk = B[k]
                for j in range(n):
                    Ci[j] += a * Bk[j]

        for j in range(n):
            Ci[j] %= MOD

    return C


def mat_pow(mat, exp):
    n = len(mat)
    res = [[0] * n for _ in range(n)]

    for i in range(n):
        res[i][i] = 1

    base = mat

    while exp > 0:
        if exp & 1:
            res = mat_mul(res, base)

        base = mat_mul(base, base)
        exp >>= 1

    return res


def vec_mul(v, mat):
    n = len(v)
    res = [0] * n

    for i in range(n):
        a = v[i]
        if a:
            Mi = mat[i]
            for j in range(n):
                res[j] += a * Mi[j]

    for j in range(n):
        res[j] %= MOD

    return res


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        N = data[idx]
        M = data[idx + 1]
        idx += 2

        A = [[0] * M for _ in range(M)]
        B = [[0] * M for _ in range(M)]

        for i in range(M):
            left = max(0, i - 1)
            right = min(M, i + 2)

            for j in range(left, right):
                B[i][j] = 1

            if i > 0:
                A[i][i - 1] = 1
            if i + 1 < M:
                A[i][i + 1] = 1

        transitions = N - 1
        pairs = transitions // 2

        v = [1] * M

        if pairs > 0:
            C = mat_mul(A, B)
            P = mat_pow(C, pairs)
            v = vec_mul(v, P)

        if transitions & 1:
            v = vec_mul(v, A)

        answers.append(str(sum(v) % MOD))

    print("\n".join(answers))


if __name__ == "__main__":
    solve()