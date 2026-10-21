import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    b = data[1:1 + 2 * n]

    max_b = max(b)

    # Smallest prime factor for every number up to max_b.
    spf = [0] * (max_b + 1)
    primes = []

    for i in range(2, max_b + 1):
        if spf[i] == 0:
            spf[i] = i
            primes.append(i)
            if i * i <= max_b:
                for j in range(i * i, max_b + 1, i):
                    if spf[j] == 0:
                        spf[j] = i

    freq = [0] * (max_b + 1)
    for x in b:
        freq[x] += 1

    keys = [i for i in range(2, max_b + 1) if freq[i] > 0]

    answer = []

    # Process composite numbers from largest to smallest.
    for x in reversed(keys):
        if freq[x] == 0:
            continue

        if spf[x] != x:  # composite
            count = freq[x]
            answer.extend([x] * count)

            greatest_proper_divisor = x // spf[x]
            freq[greatest_proper_divisor] -= count
            freq[x] = 0

    # The remaining numbers are primes. Process them from smallest to largest.
    for x in keys:
        count = freq[x]
        if count == 0:
            continue

        answer.extend([x] * count)

        # If x is prime, its generated value is the x-th prime.
        generated_prime = primes[x - 1]
        freq[generated_prime] -= count
        freq[x] = 0

    sys.stdout.write(' '.join(map(str, answer)) + '\n')


if __name__ == "__main__":
    solve()