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


def mat_vec_mul(A, v):
    x, y, z = v
    return (
        (A[0] * x + A[1] * y + A[2] * z) % MOD,
        (A[3] * x + A[4] * y + A[5] * z) % MOD,
        (A[6] * x + A[7] * y + A[8] * z) % MOD,
    )


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    queries = data[1:1 + t]

    # DFA states:
    # 0: no forbidden suffix / ends safely
    # 1: current suffix is "B"
    # 2: current suffix is "BR"
    #
    # Forbidden substrings are "BB" and "BRB".
    # These two conditions are sufficient for all prime-length substrings.
    M = (
        1, 0, 1,
        1, 0, 0,
        0, 1, 0,
    )

    powers = [M]
    for _ in range(62):
        powers.append(mat_mul(powers[-1], powers[-1]))

    answers = []

    for n in queries:
        v = (1, 0, 0)  # empty string
        exponent = n
        bit = 0

        while exponent:
            if exponent & 1:
                v = mat_vec_mul(powers[bit], v)
            exponent >>= 1
            bit += 1

        ans = (v[0] + v[1] + v[2]) % MOD
        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()