import sys

MOD = 1_000_000_007

def mat_mul(A, B):
    C = [[0] * 3 for _ in range(3)]
    for i in range(3):
        for k in range(3):
            aik = A[i][k]
            if aik:
                for j in range(3):
                    C[i][j] = (C[i][j] + aik * B[k][j]) % MOD
    return C

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    queries = data[1:1 + t]

    # f(n) = f(n-1) + f(n-3)
    # Initial values: f(0)=1, f(1)=2, f(2)=3
    A = [
        [1, 0, 1],
        [1, 0, 0],
        [0, 1, 0]
    ]

    max_bits = 61
    powers = [A]
    for _ in range(1, max_bits):
        powers.append(mat_mul(powers[-1], powers[-1]))

    def get_answer(n):
        if n == 0:
            return 1
        if n == 1:
            return 2
        if n == 2:
            return 3

        # State at n = 2: [f(2), f(1), f(0)]
        v0, v1, v2 = 3, 2, 1
        power = n - 2
        bit = 0

        while power:
            if power & 1:
                M = powers[bit]
                nv0 = (M[0][0] * v0 + M[0][1] * v1 + M[0][2] * v2) % MOD
                nv1 = (M[1][0] * v0 + M[1][1] * v1 + M[1][2] * v2) % MOD
                nv2 = (M[2][0] * v0 + M[2][1] * v1 + M[2][2] * v2) % MOD
                v0, v1, v2 = nv0, nv1, nv2

            power >>= 1
            bit += 1

        return v0

    answers = []
    for n in queries:
        answers.append(str(get_answer(n)))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()