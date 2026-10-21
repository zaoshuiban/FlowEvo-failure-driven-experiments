import sys

data = sys.stdin.buffer.read()
length = len(data)

idx = 0

# Read N
while idx < length and data[idx] <= 32:
    idx += 1

n = 0
while idx < length and data[idx] > 32:
    n = n * 10 + (data[idx] - 48)
    idx += 1

start = idx

# First pass: compute XOR of all piles
i = idx
xor_sum = 0

for _ in range(n):
    while i < length and data[i] <= 32:
        i += 1

    value = 0
    while i < length and data[i] > 32:
        value = value * 10 + (data[i] - 48)
        i += 1

    xor_sum ^= value

# If XOR is 0, the first player cannot force a win
if xor_sum == 0:
    print(0)
else:
    # Second pass: count valid first moves
    i = start
    count = 0

    for _ in range(n):
        while i < length and data[i] <= 32:
            i += 1

        value = 0
        while i < length and data[i] > 32:
            value = value * 10 + (data[i] - 48)
            i += 1

        if (value ^ xor_sum) < value:
            count += 1

    print(count)