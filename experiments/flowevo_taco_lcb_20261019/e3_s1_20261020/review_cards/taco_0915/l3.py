import sys


def main() -> None:
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

        a = [0] * n
        for i in range(n):
            a[i] = next_int()

        starts = [0]
        ends = [0]
        lengths = [0]
        run_id = [0] * (n + 1)

        run_count = 0
        pos = 0

        while pos < n:
            run_count += 1
            starts.append(pos + 1)

            value = a[pos]
            j = pos

            while j < n and a[j] == value:
                run_id[j + 1] = run_count
                j += 1

            ends.append(j)
            lengths.append(j - pos)
            pos = j

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
            runs_by_length.sort(reverse=True, key=lambda x: x[0])
            middle_queries.sort(reverse=True, key=lambda x: x[0])

            bit = [0] * (run_count + 1)
            ptr = 0

            for k, lo, hi, qi in middle_queries:
                while ptr < run_count and runs_by_length[ptr][0] >= k:
                    p = runs_by_length[ptr][1]

                    while p <= run_count:
                        bit[p] += 1
                        p += p & -p

                    ptr += 1

                total = 0

                p = hi
                while p > 0:
                    total += bit[p]
                    p -= p & -p

                p = lo - 1
                while p > 0:
                    total -= bit[p]
                    p -= p & -p

                answers[qi] += total

        output.extend(map(str, answers))

    sys.stdout.write("\n".join(output))
    if output:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()