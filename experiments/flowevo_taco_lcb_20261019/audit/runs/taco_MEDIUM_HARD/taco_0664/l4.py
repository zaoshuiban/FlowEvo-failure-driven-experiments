import sys
from collections import deque


def solve_case(n, k, p, a, ops):
    answers = []
    total_ones = sum(a)

    if k >= n:
        for ch in ops:
            if ch == '?':
                answers.append(str(total_ones))
        return answers

    # For a rotation whose first element is a[start], the answer is the
    # maximum sum among length-k windows starting at start, start+1, ...,
    # start + (n-k). We compute all these circular window sums on a doubled array.
    m = n - k + 1                 # number of windows in one rotation
    prefix = [0] * (2 * n + 1)

    for i in range(2 * n):
        prefix[i + 1] = prefix[i] + a[i % n]

    # We need window sums for starts 0 .. (2*n-k-1)
    starts_count = 2 * n - k
    best = [0] * n

    dq = deque()  # stores (index, window_sum), decreasing by window_sum

    for i in range(starts_count):
        window_sum = prefix[i + k] - prefix[i]

        while dq and dq[-1][1] <= window_sum:
            dq.pop()
        dq.append((i, window_sum))

        left = i - m + 1
        while dq and dq[0][0] < left:
            dq.popleft()

        if 0 <= left < n:
            best[left] = dq[0][1]

    start = 0
    for ch in ops:
        if ch == '?':
            answers.append(str(best[start]))
        elif ch == '!':
            start -= 1
            if start < 0:
                start = n - 1

    return answers


def main():
    raw = sys.stdin.buffer.read()
    if not raw:
        return

    tokens = raw.split()

    # The original problem has a single test case. The detection below also
    # supports the common variant where the first line contains T.
    first_non_empty = None
    for line in raw.splitlines():
        if line.strip():
            first_non_empty = line.strip()
            break

    has_t = first_non_empty is not None and len(first_non_empty.split()) == 1

    idx = 0
    test_cases_left = None
    if has_t:
        t = int(tokens[0])
        idx = 1
        test_cases_left = t

    all_answers = []
    cases_done = 0

    while idx < len(tokens) and (test_cases_left is None or cases_done < test_cases_left):
        n = int(tokens[idx])
        k = int(tokens[idx + 1])
        p = int(tokens[idx + 2])
        idx += 3

        a = list(map(int, tokens[idx:idx + n]))
        idx += n

        op_parts = []
        op_len = 0
        while idx < len(tokens) and op_len < p:
            need = p - op_len
            part = tokens[idx][:need]
            op_parts.append(part)
            op_len += len(part)
            idx += 1

        ops = b"".join(op_parts).decode()
        all_answers.extend(solve_case(n, k, p, a, ops))
        cases_done += 1

    sys.stdout.write("\n".join(all_answers))
    if all_answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()