import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    ptr = 0
    n = data[ptr]
    q = data[ptr + 1]
    ptr += 2

    a = data[ptr:ptr + n]
    ptr += n

    # prefix[p] = A[0] xor A[1] xor ... xor A[p]
    base = [0] * n
    cur = 0
    for i in range(n):
        cur ^= a[i]
        base[i] = cur

    block_size = int(n ** 0.5) + 1
    block_count = (n + block_size - 1) // block_size

    lazy = [0] * block_count
    freq = []

    for b in range(block_count):
        start = b * block_size
        end = min(n, start + block_size)
        d = {}
        for p in range(start, end):
            v = base[p]
            d[v] = d.get(v, 0) + 1
        freq.append(d)

    answers = []

    for _ in range(q):
        typ = data[ptr]
        x = data[ptr + 1]
        y = data[ptr + 2]
        ptr += 3

        if typ == 1:
            idx = x - 1
            new_value = y

            old_value = a[idx]
            delta = old_value ^ new_value

            if delta == 0:
                a[idx] = new_value
                continue

            a[idx] = new_value

            b = idx // block_size
            start = b * block_size
            end = min(n, start + block_size)

            if idx == start:
                # The whole block and all later blocks are affected.
                for bb in range(b, block_count):
                    lazy[bb] ^= delta
            else:
                # Update only the suffix part inside this block.
                d = freq[b]
                for p in range(idx, end):
                    old_v = base[p]
                    new_v = old_v ^ delta
                    base[p] = new_v

                    cnt = d[old_v] - 1
                    if cnt:
                        d[old_v] = cnt
                    else:
                        del d[old_v]

                    d[new_v] = d.get(new_v, 0) + 1

                # All blocks after this one are fully affected.
                for bb in range(b + 1, block_count):
                    lazy[bb] ^= delta

        else:
            # Count prefix xor values at positions 0 ... x-1 that equal y.
            right = x
            k = y
            result = 0

            full_blocks = right // block_size

            for b in range(full_blocks):
                result += freq[b].get(k ^ lazy[b], 0)

            start = full_blocks * block_size
            if start < right:
                b = full_blocks
                lz = lazy[b]
                for p in range(start, right):
                    if (base[p] ^ lz) == k:
                        result += 1

            answers.append(str(result))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()