import sys

def solve():
    data = sys.stdin.buffer.read()
    L = len(data)
    i = 0

    # Read N
    while i < L and not (48 <= data[i] <= 57):
        i += 1
    n = 0
    while i < L and 48 <= data[i] <= 57:
        n = n * 10 + (data[i] - 48)
        i += 1

    start = i  # position after N

    # First pass: compute XOR of all pile sizes
    xor_sum = 0
    j = i
    for _ in range(n):
        while j < L and not (48 <= data[j] <= 57):
            j += 1
        val = 0
        while j < L and 48 <= data[j] <= 57:
            val = val * 10 + (data[j] - 48)
            j += 1
        xor_sum ^= val

    # No winning first move if XOR is zero
    if xor_sum == 0:
        sys.stdout.write("0\n")
        return

    # A pile can be reduced to make XOR zero iff it has
    # the highest set bit of xor_sum set.
    msb = 1 << (xor_sum.bit_length() - 1)

    ans = 0
    j = start
    for _ in range(n):
        while j < L and not (48 <= data[j] <= 57):
            j += 1
        val = 0
        while j < L and 48 <= data[j] <= 57:
            val = val * 10 + (data[j] - 48)
            j += 1
        if val & msb:
            ans += 1

    sys.stdout.write(str(ans) + "\n")


if __name__ == "__main__":
    solve()