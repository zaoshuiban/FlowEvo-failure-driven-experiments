import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    A = data[1:1 + n]

    m = max(A)

    freq = [0] * (m + 2)
    for x in A:
        freq[x] += 1

    prefix = [0] * (m + 2)
    total_count = 0
    for i in range(1, m + 1):
        total_count += freq[i]
        prefix[i] = total_count

    ans = 0

    # Pairs with equal values
    for x in range(1, m + 1):
        c = freq[x]
        if c >= 2:
            ans += c * (c - 1) // 2

    # Pairs with different values: count floor(larger / smaller)
    for a in range(1, m + 1):
        c = freq[a]
        if c == 0:
            continue

        total = 0

        # Quotient 1: b in [a + 1, 2a - 1]
        left = a + 1
        right = min(m, 2 * a - 1)
        if left <= right:
            total += prefix[right] - prefix[left - 1]

        # Quotients >= 2
        qmax = m // a
        left = 2 * a

        for q in range(2, qmax + 1):
            right = min(m, (q + 1) * a - 1)
            if left <= right:
                total += q * (prefix[right] - prefix[left - 1])
            left += a

        ans += c * total

    print(ans)


if __name__ == "__main__":
    main()