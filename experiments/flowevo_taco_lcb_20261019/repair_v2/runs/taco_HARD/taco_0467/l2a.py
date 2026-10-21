import sys

MOD = 998244353

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    N = int(data[0])
    P = int(data[1])

    invP = pow(P % MOD, MOD - 2, MOD)
    inv4 = pow(4, MOD - 2, MOD)

    r = 1
    A = 0  # sum P^{-(j-1)}
    B = 0  # sum P^{-2(j-1)}

    ans = []

    for _ in range(N):
        A = (A + r) % MOD
        B = (B + r * r) % MOD

        value = (A * A + B) % MOD
        value = value * inv4 % MOD
        ans.append(str(value))

        r = r * invP % MOD

    sys.stdout.write(" ".join(ans))

if __name__ == "__main__":
    main()