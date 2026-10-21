import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]

    max_sum = max(a) * 2

    # Sum of f(2 * A_i) over all i.
    # Since f(2x) = f(x), this is sum of odd parts of A_i.
    odd_sum = 0
    for x in a:
        odd_sum += x // (x & -x)

    # total = sum_{i,j} f(A_i + A_j), over all ordered pairs.
    total = 0
    target = 1  # target = 2^k

    while target <= max_sum:
        mod_mask = (target << 1) - 1
        groups = {}

        for x in a:
            r = x & mod_mask
            prev = groups.get(r)
            if prev is None:
                groups[r] = (1, x)
            else:
                groups[r] = (prev[0] + 1, prev[1] + x)

        subtotal = 0

        for r, (cnt, sm) in groups.items():
            q = (target - r) & mod_mask
            other = groups.get(q)
            if other is not None:
                cnt2, sm2 = other
                subtotal += cnt * sm2 + cnt2 * sm

        total += subtotal // target
        target <<= 1

    answer = (total + odd_sum) // 2
    print(answer)

if __name__ == "__main__":
    main()