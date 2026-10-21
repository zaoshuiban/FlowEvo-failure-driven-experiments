import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))

    n = data[0]

    q_pos = 1 + 2 * n
    q = data[q_pos]
    queries = data[q_pos + 1: q_pos + 1 + q]

    m = max(queries)

    size = 1
    while size < m:
        size <<= 1

    neg_inf = -10**15

    # d[node] = maximum value in this node's segment,
    # including lazy[node] but excluding ancestors' lazy values.
    d = [neg_inf] * (2 * size)
    lazy = [0] * (2 * size)

    for i in range(m):
        d[size + i] = i + 1

    for i in range(size - 1, 0, -1):
        d[i] = max(d[i << 1], d[i << 1 | 1])

    def first_ge(target):
        """Return the first index whose current value is >= target, or m if none."""
        if d[1] < target:
            return m

        node = 1
        carry = 0

        while node < size:
            carry += lazy[node]
            left = node << 1
            if d[left] + carry >= target:
                node = left
            else:
                node = left | 1

        pos = node - size
        return pos if pos < m else m

    def add_range(left, right):
        """Add 1 to [left, right)."""
        left += size
        right += size
        left0 = left
        right0 = right

        while left < right:
            if left & 1:
                d[left] += 1
                lazy[left] += 1
                left += 1
            if right & 1:
                right -= 1
                d[right] += 1
                lazy[right] += 1
            left >>= 1
            right >>= 1

        left = left0 >> 1
        right = (right0 - 1) >> 1

        while left:
            lc = left << 1
            d[left] = max(d[lc], d[lc | 1]) + lazy[left]

            lc = right << 1
            d[right] = max(d[lc], d[lc | 1]) + lazy[right]

            left >>= 1
            right >>= 1

    idx = 1
    for _ in range(n):
        l = data[idx]
        r = data[idx + 1]
        idx += 2

        a = first_ge(l)
        if a == m:
            continue

        b = first_ge(r + 1)
        if a < b:
            add_range(a, b)

    # Propagate all lazy values to the leaves.
    for k in range(1, size):
        z = lazy[k]
        if z:
            lc = k << 1
            rc = lc | 1
            d[lc] += z
            lazy[lc] += z
            d[rc] += z
            lazy[rc] += z

    answers = [str(d[size + x - 1]) for x in queries]
    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()