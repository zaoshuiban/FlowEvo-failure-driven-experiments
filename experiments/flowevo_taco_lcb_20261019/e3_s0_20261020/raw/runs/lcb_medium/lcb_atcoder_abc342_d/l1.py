import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    max_a = max(a)

    # Smallest prime factor sieve
    spf = list(range(max_a + 1))
    if max_a >= 1:
        spf[1] = 1

    limit = int(max_a ** 0.5)
    for i in range(2, limit + 1):
        if spf[i] == i:
            for j in range(i * i, max_a + 1, i):
                if spf[j] == j:
                    spf[j] = i

    zero_count = 0
    kernel_count = {}

    for value in a:
        if value == 0:
            zero_count += 1
            continue

        x = value
        kernel = 1

        while x > 1:
            p = spf[x]
            parity = 0

            while x % p == 0:
                x //= p
                parity ^= 1

            if parity:
                kernel *= p

        kernel_count[kernel] = kernel_count.get(kernel, 0) + 1

    # Pairs containing at least one zero
    ans = zero_count * (n - zero_count) + zero_count * (zero_count - 1) // 2

    # Pairs of positive numbers with the same square-free kernel
    for count in kernel_count.values():
        ans += count * (count - 1) // 2

    print(ans)


if __name__ == "__main__":
    main()