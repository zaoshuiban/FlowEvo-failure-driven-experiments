import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, K, Q = data[0], data[1], data[2]

    value_set = set(data[4::2])
    value_set.add(0)
    values = sorted(value_set)

    M = len(values)
    pos = {v: i + 1 for i, v in enumerate(values)}

    zero_pos = pos[0]
    current = [zero_pos] * (N + 1)

    bit_count = [0] * (M + 1)
    bit_sum = [0] * (M + 1)

    i = zero_pos
    while i <= M:
        bit_count[i] += N
        i += i & -i

    total_sum = 0
    smallest_count = N - K
    highest_bit = 1 << (M.bit_length() - 1)

    answers = []
    p = 3

    for _ in range(Q):
        x = data[p]
        y = data[p + 1]
        p += 2

        old_pos = current[x]
        new_pos = pos[y]

        if old_pos != new_pos:
            old_value = values[old_pos - 1]

            i = old_pos
            while i <= M:
                bit_count[i] -= 1
                bit_sum[i] -= old_value
                i += i & -i

            i = new_pos
            while i <= M:
                bit_count[i] += 1
                bit_sum[i] += y
                i += i & -i

            current[x] = new_pos
            total_sum += y - old_value

        if smallest_count == 0:
            answers.append(str(total_sum))
            continue

        target = smallest_count
        idx = 0
        count = 0
        part_sum = 0
        step = highest_bit

        while step:
            nxt = idx + step
            if nxt <= M and count + bit_count[nxt] < target:
                idx = nxt
                count += bit_count[nxt]
                part_sum += bit_sum[nxt]
            step >>= 1

        threshold = values[idx]
        remaining = target - count
        smallest_sum = part_sum + remaining * threshold

        answers.append(str(total_sum - smallest_sum))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()