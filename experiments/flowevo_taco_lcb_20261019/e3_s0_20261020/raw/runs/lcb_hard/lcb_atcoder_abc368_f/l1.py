import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N = data[0]
    A = data[1:1 + N]

    M = max(A)

    # Smallest prime factor sieve
    spf = list(range(M + 1))
    if M >= 1:
        spf[1] = 1

    for i in range(2, int(M ** 0.5) + 1):
        if spf[i] == i:
            for j in range(i * i, M + 1, i):
                if spf[j] == j:
                    spf[j] = i

    # omega[x] = number of prime factors of x counted with multiplicity
    omega = [0] * (M + 1)
    for i in range(2, M + 1):
        omega[i] = omega[i // spf[i]] + 1

    xor_sum = 0
    for a in A:
        xor_sum ^= omega[a]

    print("Anna" if xor_sum != 0 else "Bruno")


if __name__ == "__main__":
    main()