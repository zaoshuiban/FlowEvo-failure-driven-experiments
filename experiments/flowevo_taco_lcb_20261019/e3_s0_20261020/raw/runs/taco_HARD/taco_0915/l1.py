import sys


def int_iter(data):
    n = len(data)
    i = 0
    while i < n:
        while i < n and data[i] <= 32:
            i += 1
        if i >= n:
            break
        num = 0
        while i < n and data[i] > 32:
            num = num * 10 + (data[i] - 48)
            i += 1
        yield num


def solve():
    data = sys.stdin.buffer.read()
    it = int_iter(data)

    try:
        T = next(it)
    except StopIteration:
        return

    output = []

    for _ in range(T):
        N = next(it)
        Q = next(it)

        A = [0] * (N + 1)
        for i in range(1, N + 1):
            A[i] = next(it)

        run_id = [0] * (N + 1)

        starts = [0]
        ends = [0]
        lengths = [0]

        run_count = 0
        pos = 1

        while pos <= N:
            end = pos
            value = A[pos]

            while end < N and A[end + 1] == value:
                end += 1

            run_count += 1
            starts.append(pos)
            ends.append(end)
            lengths.append(end - pos + 1)

            for p in range(pos, end + 1):
                run_id[p] = run_count

            pos = end + 1

        answers = [0] * Q
        events = []

        for qi in range(Q):
            L = next(it)
            R = next(it)
            K = next(it)

            left_run = run_id[L]
            right_run = run_id[R]

            if left_run == right_run:
                answers[qi] = 1 if R - L + 1 >= K else 0
            else:
                left_length = ends[left_run] - L + 1
                right_length = R - starts[right_run] + 1

                count = 0
                if left_length >= K:
                    count += 1
                if right_length >= K:
                    count += 1

                answers[qi] = count

                l = left_run + 1
                r = right_run - 1

                if l <= r:
                    events.append((K, l, r, qi))

        if events:
            order = list(range(1, run_count + 1))
            order.sort(key=lengths.__getitem__, reverse=True)

            events.sort(key=lambda x: x[0], reverse=True)

            fenwick = [0] * (run_count + 1)
            pointer = 0

            for K, l, r, qi in events:
                while pointer < run_count and lengths[order[pointer]] >= K:
                    idx = order[pointer]

                    while idx <= run_count:
                        fenwick[idx] += 1
                        idx += idx & -idx

                    pointer += 1

                total = 0

                idx = r
                while idx > 0:
                    total += fenwick[idx]
                    idx -= idx & -idx

                idx = l - 1
                while idx > 0:
                    total -= fenwick[idx]
                    idx -= idx & -idx

                answers[qi] += total

        for answer in answers:
            output.append(str(answer))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()