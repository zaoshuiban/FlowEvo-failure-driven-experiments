import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    max_value = max(data)  # n may be larger than all b-values, which is harmless

    freq = [0] * (max_value + 1)
    for i in range(1, len(data)):
        freq[data[i]] += 1

    # Sieve primes up to max_value
    is_prime = bytearray(b'\x01') * (max_value + 1)
    if max_value >= 0:
        is_prime[0] = 0
    if max_value >= 1:
        is_prime[1] = 0

    root = int(max_value ** 0.5)
    for i in range(2, root + 1):
        if is_prime[i]:
            start = i * i
            is_prime[start:max_value + 1:i] = b'\x00' * (((max_value - start) // i) + 1)

    primes = []
    for i in range(2, max_value + 1):
        if is_prime[i]:
            primes.append(i)

    # Maps prime p_i to its index i
    prime_index = {p: i + 1 for i, p in enumerate(primes)}

    # Smallest prime factors up to 200000
    LIM = 200000
    spf = list(range(LIM + 1))
    root = int(LIM ** 0.5)

    for i in range(2, root + 1):
        if spf[i] == i:
            for j in range(i * i, LIM + 1, i):
                if spf[j] == j:
                    spf[j] = i

    ans = []

    for x in range(max_value, 1, -1):
        while freq[x] > 0:
            if is_prime[x]:
                # x is the prime appended for original value y
                y = prime_index[x]
                freq[x] -= 1
                freq[y] -= 1
                ans.append(y)
            else:
                # x is an original composite number
                y = x // spf[x]  # greatest proper divisor of x
                freq[x] -= 1
                freq[y] -= 1
                ans.append(x)

    sys.stdout.write(" ".join(map(str, ans)))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()