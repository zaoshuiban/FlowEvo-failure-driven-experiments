import sys
from collections import deque


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    idx = 0
    n = int(data[idx]); idx += 1
    k = int(data[idx]); idx += 1
    p = int(data[idx]); idx += 1

    a = list(map(int, data[idx:idx + n])); idx += n
    operations = data[idx] if idx < len(data) else b''

    total_ones = sum(a)
    answers = []

    # If the frame can cover the whole array, every rotation gives the same answer.
    if k >= n:
        for ch in operations:
            if ch == ord('?'):
                answers.append(str(total_ones))
        sys.stdout.write("\n".join(answers))
        return

    # window_sums[i] = number of ones in a circular segment of length k starting at i
    window_sums = [0] * n
    current = sum(a[:k])
    window_sums[0] = current

    for start in range(1, n):
        current -= a[start - 1]
        add_index = start + k - 1
        if add_index >= n:
            add_index -= n
        current += a[add_index]
        window_sums[start] = current

    # For a given rotation, valid starts form a circular interval of this length.
    interval_len = n - k + 1

    # doubled_sums allows circular interval maximum queries.
    doubled_sums = window_sums + window_sums

    # best[start] = maximum window_sums in [start, start + interval_len - 1] circularly
    best = [0] * n
    dq = deque()

    for i in range(interval_len):
        while dq and doubled_sums[dq[-1]] <= doubled_sums[i]:
            dq.pop()
        dq.append(i)

    best[0] = doubled_sums[dq[0]]

    for start in range(1, n):
        while dq and dq[0] < start:
            dq.popleft()

        right = start + interval_len - 1
        while dq and doubled_sums[dq[-1]] <= doubled_sums[right]:
            dq.pop()
        dq.append(right)

        best[start] = doubled_sums[dq[0]]

    # current_start = original index of the current first element after right shifts.
    current_start = 0

    for ch in operations:
        if ch == ord('!'):
            current_start -= 1
            if current_start < 0:
                current_start += n
        elif ch == ord('?'):
            answers.append(str(best[current_start]))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()