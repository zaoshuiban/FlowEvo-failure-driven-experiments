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

    # First pass: compute XOR of all pile sizes
    xor_sum = 0
    start = i
    for _ in range(n):
        while i < L and not (48 <= data[i] <= 57):
            i += 1
        val = 0
        while i < L and 48 <= data[i] <= 57:
            val = val * 10 + (data[i] - 48)
            i += 1
        xor_sum ^= val

    # If XOR is zero, the first player cannot force a win
    if xor_sum == 0:
        sys.stdout.write("0")
        return

    # Second pass: count winning first moves
    i = start
    count = 0
    for _ in range(n):
        while i < L and not (48 <= data[i] <= 57):
            i += 1
        val = 0
        while i < L and 48 <= data[i] <= 57:
            val = val * 10 + (data[i] - 48)
            i += 1
        # A valid move exists iff reducing this pile to (val ^ xor_sum) is possible
        if (val ^ xor_sum) < val:
            count += 1

    sys.stdout.write(str(count))

if __name__ == "__main__":
    solve()