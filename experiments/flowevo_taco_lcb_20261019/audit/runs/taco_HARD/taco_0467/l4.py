import sys

MOD = 998244353

def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    N = int(data[0])
    P = int(data[1])

    invP = pow(P, MOD - 2, MOD)
    invP2 = invP * invP % MOD

    inv2 = (MOD + 1) // 2
    inv4 = inv2 * inv2 % MOD

    # A_i = sum_{k=0}^{i-1} P^{-k}
    # B_i = sum_{k=0}^{i-1} P^{-2k}
    # F(i) = (A_i^2 + B_i) / 4
    A = 0
    B = 0
    term = 1       # P^{-k}
    term_sq = 1    # P^{-2k}

    ans = []

    for _ in range(N):
        A = (A + term) % MOD
        B = (B + term_sq) % MOD

        f = (A * A + B) % MOD
        f = f * inv4 % MOD
        ans.append(str(f))

        term = term * invP % MOD
        term_sq = term_sq * invP2 % MOD

    sys.stdout.write(" ".join(ans) + "\n")


if __name__ == "__main__":
    main()