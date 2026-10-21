import sys


def main():
    data = sys.stdin.buffer.read()
    idx = 0
    data_len = len(data)

    def next_int():
        nonlocal idx
        while idx < data_len and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < data_len and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    output = []

    for _ in range(t):
        n = next_int()
        q = next_int()

        run_id = [0] * (n + 1)

        starts = [0]
        ends = [0]
        lengths = [0]

        prev = None
        current_start = 1
        current_run = 1

        for i in range(1, n + 1):
            x = next_int()

            if i == 1:
                prev = x
                current_start = 1
                current_run = 1
            elif x != prev:
                starts.append(current_start)
                ends.append(i - 1)
                lengths.append((i - 1) - current_start + 1)

                current_start = i
                current_run = len(starts)
                prev = x

            run_id[i] = current_run

        starts.append(current_start)
        ends.append(n)
        lengths.append(n - current_start + 1)

        run_count = len(starts) - 1

        answers = [0] * q
        middle_queries = []

        for qi in range(q):
            left = next_int()
            right = next_int()
            k = next_int()

            left_run = run_id[left]
            right_run = run_id[right]

            if left_run == right_run:
                answers[qi] = 1 if right - left + 1 >= k else 0
                continue

            count = 0

            left_part_length = ends[left_run] - left + 1
            if left_part_length >= k:
                count += 1

            right_part_length = right - starts[right_run] + 1
            if right_part_length >= k:
                count += 1

            answers[qi] = count

            lo = left_run + 1
            hi = right_run - 1

            if lo <= hi:
                middle_queries.append((k, lo, hi, qi))

        if middle_queries:
            runs_by_length = [(lengths[i], i) for i in range(1, run_count + 1)]
            runs_by_length.sort(reverse=True)
            middle_queries.sort(reverse=True)

            bit = [0] * (run_count + 1)
            ptr = 0

            for k, lo, hi, qi in middle_queries:
                while ptr < run_count and runs_by_length[ptr][0] >= k:
                    pos = runs_by_length[ptr][1]

                    while pos <= run_count:
                        bit[pos] += 1
                        pos += pos & -pos

                    ptr += 1

                total = 0

                pos = hi
                while pos > 0:
                    total += bit[pos]
                    pos -= pos & -pos

                pos = lo - 1
                while pos > 0:
                    total -= bit[pos]
                    pos -= pos & -pos

                answers[qi] += total

        output.extend(map(str, answers))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()