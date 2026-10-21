```python
import sys
import random


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    p = int(data[2])

    rows = data[3:3 + n]
    row_masks = []
    max_likes = 0

    for s in rows:
        mask = 0
        for j, ch in enumerate(s):
            if ch == 49:  # ord('1')
                mask |= 1 << j
        row_masks.append(mask)
        bc = mask.bit_count()
        if bc > max_likes:
            max_likes = bc

    need = (n + 1) // 2

    if max_likes == 0:
        sys.stdout.write('0' * m)
        return

    trials = min(n, 60)
    if trials == n:
        anchors = list(range(n))
    else:
        anchors = random.sample(range(n), trials)

    CH = 15
    num_chunks = (m + CH - 1) // CH
    chunk_shifts = []
    chunk_masks = []

    for c in range(num_chunks):
        off = c * CH
        bits_in_chunk = min(CH, m - off)
        chunk_shifts.append(off)
        chunk_masks.append((1 << bits_in_chunk) - 1)

    best_size = 0
    answer_mask = 0

    for row_id in anchors:
        anchor = row_masks[row_id]

        positions = []
        tmp = anchor
        while tmp:
            lsb = tmp & -tmp
            pos = lsb.bit_length() - 1
            positions.append(pos)
            tmp ^= lsb

        k = len(positions)
        if k <= best_size:
            continue

        active_tables = []
        active_shifts = []
        active_masks = []

        for c in range(num_chunks):
            off = chunk_shifts[c]
            bits_in_chunk = min(CH, m - off)

            has_position = False
            for pos in positions:
                if off <= pos < off + bits_in_chunk:
                    has_position = True
                    break

            if not has_position:
                continue

            size = 1 << bits_in_chunk
            table = [0] * size

            for comp_idx, pos in enumerate(positions):
                if off <= pos < off + bits_in_chunk:
                    local_bit = 1 << (pos - off)
                    comp_bit = 1 << comp_idx
                    step = local_bit << 1

                    for base in range(0, size, step):
                        end = base + step
                        for v in range(base + local_bit, end):
                            table[v] |= comp_bit

            active_tables.append(table)
            active_shifts.append(off)
            active_masks.append((1 << bits_in_chunk) - 1)

        total_masks = 1 << k
        freq = [0] * total_masks

        ac = len(active_tables)

        if ac == 1:
            t0 = active_tables[0]
            s0 = active_shifts[0]
            m0 = active_masks[0]

            for x in row_masks:
                b = t0[(x >> s0) & m0]
                freq[b] += 1

        elif ac == 2:
            t0 = active_tables[0]
            s0 = active_shifts[0]
            m0 = active_masks[0]
            t1 = active_tables[1]
            s1 = active_shifts[1]
            m1 = active_masks[1]

            for x in row_masks:
                b = t0[(x >> s0) & m0] | t1[(x >> s1) & m1]
                freq[b] += 1

        elif ac == 3:
            t0 = active_tables[0]
            s0 = active_shifts[0]
            m0 = active_masks[0]
            t1 = active_tables[1]
            s1 = active_shifts[1]
            m1 = active_masks[1]
            t2 = active_tables[2]
            s2 = active_shifts[2]
            m2 = active_masks[2]

            for x in row_masks:
                b = (
                    t0[(x >> s0) & m0]
                    | t1[(x >> s1) & m1]
                    | t2[(x >> s2) & m2]
                )
                freq[b] += 1

        elif ac == 4:
            t0 = active_tables[0]
            s0 = active_shifts[0]
            m0 = active_masks[0]
            t1 = active_tables[1]
            s1 = active_shifts[1]
            m1 = active_masks[1]
            t2 = active_tables[2]
            s2 = active_shifts[2]
            m2 = active_masks[2]
            t3 = active_tables[3]
            s3 = active_shifts[3]
            m3 = active_masks[3]

            for x in row_masks:
                b = (
                    t0[(x >> s0) & m0]
                    | t1[(x >> s1) & m1]
                    | t2[(x >> s2) & m2]
                    | t3[(x >> s3) & m3]
                )
                freq[b] += 1

        else:
            for x in row_masks:
                b = 0
                for i in range(ac):
                    b |= active_tables[i][(x >> active_shifts[i]) & active_masks[i]]
                freq[b] += 1

        full = total_masks - 1

        if freq[full] >= need:
            if k > best_size:
                best_size = k
                answer_mask = anchor

            if best_size == max_likes:
                break
            continue

        support = freq

        for i in range(k):
            step = 1 << i
            step2 = step << 1

            for base in range(0, total_masks, step2):
                end = base + step
                for mask in range(base, end):
                    support[mask] += support[mask + step]

        if k <= best_size:
            continue

        for mask, cnt in enumerate(support):
            if cnt >= need:
                cur_size = mask.bit_count()

                if cur_size > best_size:
                    cur_answer = 0

                    for comp_idx, pos in enumerate(positions):
                        if (mask >> comp_idx) & 1:
                            cur_answer |= 1 << pos

                    best_size = cur_size
                    answer_mask = cur_answer

                    if best_size == max_likes:
                        break

        if best_size == max_likes:
            break

    result = ['0'] * m
    for j in range(m):
        if (answer_mask >> j) & 1:
            result[j] = '1'

    sys.stdout.write(''.join(result))


if __name__ == "__main__":
    solve