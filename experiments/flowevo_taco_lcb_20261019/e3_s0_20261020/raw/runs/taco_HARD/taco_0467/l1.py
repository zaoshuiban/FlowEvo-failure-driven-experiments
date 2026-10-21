import sys

MOD = 998244353
INV2 = (MOD + 1) // 2

def main():
    N, P = map(int, sys.stdin.readline().split())

    invP = pow(P, MOD - 2, MOD)

    a = 1                      # a_i = P^{-(i-1)}
    mean = 0                   # E[S_{i-1}]
    expected_square = 0        # F(i-1)
    ans = []

    for _ in range(N):
        term = (mean * a + a * a % MOD * INV2) % MOD
        expected_square = (expected_square + term) % MOD
        ans.append(str(expected_square))

        mean = (mean + a * INV2) % MOD
        a = a * invP % MOD

    sys.stdout.write(" ".join(ans))

if __name__ == "__main__":
    main()