import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0

    n = data[idx]
    idx += 1

    arr = data[idx:idx + n]
    idx += n

    m = data[idx]
    idx += 1

    BLOCK = 1024
    num_blocks = (n + BLOCK - 1) // BLOCK
    primes = (2, 3, 5)

    masks = {p: [0] * num_blocks for p in primes}

    for i, value in enumerate(arr):
        b = i // BLOCK
        bit = 1 << (i % BLOCK)
        for p in primes:
            if value % p == 0:
                masks[p][b] |= bit

    for _ in range(m):
        query_type = data[idx]
        idx += 1

        if query_type == 1:
            l = data[idx] - 1
            r = data[idx + 1] - 1
            p = data[idx + 2]
            idx += 3

            left_block = l // BLOCK
            right_block = r // BLOCK
            block_masks = masks[p]

            for b in range(left_block, right_block + 1):
                base = b * BLOCK

                if b > left_block and b < right_block:
                    bits = block_masks[b]
                else:
                    left = l - base if b == left_block else 0
                    right = r - base if b == right_block else BLOCK - 1
                    length = right - left + 1
                    range_mask = ((1 << length) - 1) << left
                    bits = block_masks[b] & range_mask

                while bits:
                    low_bit = bits & -bits
                    offset = low_bit.bit_length() - 1
                    pos = base + offset

                    value = arr[pos] // p
                    arr[pos] = value

                    if value % p != 0:
                        block_masks[b] ^= low_bit

                    bits ^= low_bit

        else:
            pos = data[idx] - 1
            new_value = data[idx + 1]
            idx += 2

            arr[pos] = new_value
            b = pos // BLOCK
            bit = 1 << (pos % BLOCK)

            for p in primes:
                if new_value % p == 0:
                    masks[p][b] |= bit
                else:
                    masks[p][b] &= ~bit

    sys.stdout.write(" ".join(map(str, arr)))


if __name__ == "__main__":
    main()