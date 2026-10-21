import sys
import random


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    p = int(data[2])

    # Bit j represents whether the friend likes currency j.
    rows = [int(s[::-1], 2) for s in data[3:3 + n]]

    need = (n + 1) // 2
    max_likes = max(x.bit_count() for x in rows)

    if max_likes == 0:
        sys.stdout.write("0" * m)
        return

    # Any optimal non-empty subset is contained in the liked set of some
    # friend who likes all currencies of that subset. Sampling friends gives
    # a high-probability way to find such an anchor.
    if n <= 60:
        anchors = list(range(n))
    else:
        anchors = random.sample(range(n), 60)

    anchors.sort(key=lambda idx: rows[idx].bit_count(), reverse=True)

    best_size = 0
    answer_mask = 0

    CHUNK = 15
    chunks = []
    for off in range(0, m, CHUNK):
        bits = min(CHUNK, m - off)
        chunks.append((off, (1 << bits) - 1, bits))

    MAXV = 1 << CHUNK

    lsb_idx = [0] * MAXV
    for v in range(1, MAXV):
        lsb_idx[v] = (v & -v).bit_length() - 1

    popcount = [0] * MAXV
    for v in range(1, MAXV):
        popcount[v] = popcount[v >> 1] + (v & 1)

    for row_id in anchors:
        anchor = rows[row_id]
        k = anchor.bit_count()

        if k <= best_size:
            continue

        positions = []
        tmp = anchor
        while tmp:
            lb = tmp & -tmp
            positions.append(lb.bit_length() - 1)
            tmp ^= lb

        active = []

        for off, mask, bits in chunks:
            if anchor & (mask << off):
                size = 1 << bits
                table = [0] * size
                local_comp = [0] * bits

                for idx, pos in enumerate(positions):
                    if off <= pos < off + bits:
                        local_comp[pos - off] = 1 << idx

                for v in range(1, size):
                    bi = lsb_idx[v]
                    table[v] = table[v ^ (1 << bi)] | local_comp[bi]

                active.append((off, mask, table))

        total = 1 << k
        freq = [0] * total

        ac = len(active)

        if ac == 1:
            off0, mask0, tab0 = active[0]
            for x in rows:
                freq[tab0[(x >> off0) & mask0]] += 1

        elif ac == 2:
            off0, mask0, tab0 = active[0]
            off1, mask1, tab1 = active[1]
            for x in rows:
                y = tab0[(x >> off0) & mask0] | tab1[(x >> off1) & mask1]
                freq[y] += 1

        elif ac == 3:
            off0, mask0, tab0 = active[0]
            off1, mask1, tab1 = active[1]
            off2, mask2, tab2 = active[2]
            for x in rows:
                y = (
                    tab0[(x >> off0) & mask0]
                    | tab1[(x >> off1) & mask1]
                    | tab2[(x >> off2) & mask2]
                )
                freq[y] += 1

        elif ac == 4:
            off0, mask0, tab0 = active[0]
            off1, mask1, tab1 = active[1]
            off2, mask2, tab2 = active[2]
            off3, mask3, tab3 = active[3]
            for x in rows:
                y = (
                    tab0[(x >> off0) & mask0]
                    | tab1[(x >> off1) & mask1]
                    | tab2[(x >> off2) & mask2]
                    | tab3[(x >> off3) & mask3]
                )
                freq[y] += 1

        else:
            for x in rows:
                y = 0
                for off, mask, table in active:
                    y |= table[(x >> off) & mask]
                freq[y] += 1

        # Superset sum: after this, freq[S] is the number of friends
        # whose compressed liked mask contains S.
        arr = freq
        for i in range(k):
            step = 1 << i
            step2 = step << 1
            for base in range(0, total, step2):
                end = base + step
                for s in range(base, end):
                    arr[s] += arr[s + step]

        if arr[total - 1] >= need:
            best_size = k
            answer_mask = anchor
            if best_size == max_likes:
                break
            continue

        local_best = best_size
        local_answer = answer_mask

        for s, cnt in enumerate(arr):
            if cnt >= need:
                sz = popcount[s]
                if sz > local_best:
                    local_best = sz

                    ans = 0
                    t = s
                    while t:
                        lb = t & -t
                        idx = lb.bit_length() - 1
                        ans |= 1 << positions[idx]
                        t ^= lb

                    local_answer = ans

        if local_best > best_size:
            best_size = local_best
            answer_mask = local_answer
            if best_size == max_likes:
                break

    result = ['0'] * m
    for j in range(m):
        if (answer_mask >> j) & 1:
            result[j] = '1'

    sys.stdout.write(''.join(result))


if __name__ == "__main__":
    solve()