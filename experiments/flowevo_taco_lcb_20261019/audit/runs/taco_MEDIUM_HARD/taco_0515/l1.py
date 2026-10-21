import sys

MOD = 1_000_000_007

def mat_mul(A, B):
    C = [[0] * 3 for _ in range(3)]
    for i in range(3):
        ai0, ai1, ai2 = A[i]
        C[i][0] = (ai0 * B[0][0] + ai1 * B[1][0] + ai2 * B[2][0]) % MOD
        C[i][1] = (ai0 * B[0][1] + ai1 * B[1][1] + ai2 * B[2][1]) % MOD
        C[i][2] = (ai0 * B[0][2] + ai1 * B[1][2] + ai2 * B[2][2]) % MOD
    return C

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]

    M = [
        [1, 0, 1],
        [1, 0, 0],
        [0, 1, 0]
    ]

    powers = [M]
    for _ in range(1, 61):
        powers.append(mat_mul(powers[-1], powers[-1]))

    answers = []

    for idx in range(1, t + 1):
        n = data[idx]

        if n == 0:
            answers.append("1")
            continue
        if n == 1:
            answers.append("2")
            continue
        if n == 2:
            answers.append("3")
            continue

        exp = n - 2
        v0, v1, v2 = 3, 2, 1  # [a2, a1, a0]
        bit = 0

        while exp:
            if exp & 1:
                A = powers[bit]
                nv0 = (A[0][0] * v0 + A[0][1] * v1 + A[0][2] * v2) % MOD
                nv1 = (A[1][0] * v0 + A[1][1] * v1 + A[1][2] * v2) % MOD
                nv2 = (A[2][0] * v0 + A[2][1] * v1 + A[2][2] * v2) % MOD
                v0, v1, v2 = nv0, nv1, nv2

            exp >>= 1
            bit += 1

        answers.append(str(v0))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()