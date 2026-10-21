import sys

MOD = 1_000_000_007

def mat_mul(A, B):
    a00, a01, a02, a10, a11, a12, a20, a21, a22 = A
    b00, b01, b02, b10, b11, b12, b20, b21, b22 = B

    return (
        (a00 * b00 + a01 * b10 + a02 * b20) % MOD,
        (a00 * b01 + a01 * b11 + a02 * b21) % MOD,
        (a00 * b02 + a01 * b12 + a02 * b22) % MOD,

        (a10 * b00 + a11 * b10 + a12 * b20) % MOD,
        (a10 * b01 + a11 * b11 + a12 * b21) % MOD,
        (a10 * b02 + a11 * b12 + a12 * b22) % MOD,

        (a20 * b00 + a21 * b10 + a22 * b20) % MOD,
        (a20 * b01 + a21 * b11 + a22 * b21) % MOD,
        (a20 * b02 + a21 * b12 + a22 * b22) % MOD,
    )


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    queries = data[1:1 + t]

    # Transition matrix:
    # dp[n] = dp[n-1] + dp[n-3]
    M = (
        1, 0, 1,
        1, 0, 0,
        0, 1, 0
    )

    powers = [M]
    for _ in range(61):
        powers.append(mat_mul(powers[-1], powers[-1]))

    answers = []

    for n in queries:
        if n == 0:
            ans = 1
        elif n == 1:
            ans = 2
        elif n == 2:
            ans = 3
        else:
            exponent = n - 2
            v0, v1, v2 = 3, 2, 1  # dp[2], dp[1], dp[0]

            bit = 0
            while exponent:
                if exponent & 1:
                    A = powers[bit]
                    a00, a01, a02, a10, a11, a12, a20, a21, a22 = A

                    nv0 = (a00 * v0 + a01 * v1 + a02 * v2) % MOD
                    nv1 = (a10 * v0 + a11 * v1 + a12 * v2) % MOD
                    nv2 = (a20 * v0 + a21 * v1 + a22 * v2) % MOD

                    v0, v1, v2 = nv0, nv1, nv2

                exponent >>= 1
                bit += 1

            ans = v0

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()