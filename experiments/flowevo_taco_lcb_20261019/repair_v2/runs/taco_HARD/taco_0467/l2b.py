import sys

MOD = 998244353

def main():
    data = sys.stdin.buffer.read().split()
    N = int(data[0])
    P = int(data[1])

    invP = pow(P, MOD - 2, MOD)
    inv4 = pow(4, MOD - 2, MOD)

    ans = []
    term = 1
    total = 0
    total_sq = 0

    for _ in range(N):
        total = (total + term) % MOD
        total_sq = (total_sq + term * term) % MOD

        result = (total * total + total_sq) % MOD
        result = result * inv4 % MOD
        ans.append(str(result))

        term = term * invP % MOD

    sys.stdout.write(" ".join(ans))

if __name__ == "__main__":
    main()