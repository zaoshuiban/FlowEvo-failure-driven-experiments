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

        a = [next_int() for _ in range(n)]

        # Build maximal equal-value runs.
        # run_id is 1-based.
        run_id = [0] * n
        starts = [0]      # starts[r] = 0-based inclusive start of run r
        ends = [0]        # ends[r]   = 0-based exclusive end of run r
        lengths = [0]

        run_count = 0
        pos = 0

        while pos < n:
            run_count += 1
            start = pos
            value = a[pos]

            while pos < n and a[pos] == value:
                run_id[pos] = run_count
                pos += 1

            end = pos
            starts.append(start)
            ends.append(end)
            lengths.append(end - start)

        answers = [0] * q
        middle_queries = []

        for qi in range(q):
            left = next_int() - 1
            right = next_int() - 1
            k = next_int()

            left_run = run_id[left]
            right_run = run_id[right]

            if left_run == right_run:
                answers[qi] = 1 if (right - left + 1) >= k else 0
                continue

            count = 0

            # Left boundary block.
            if ends[left_run] - left >= k:
                count += 1

            # Right boundary block.
            if right - starts[right_run] + 1 >= k:
                count += 1

            answers[qi] = count

            # Complete runs strictly between the two boundary runs.
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