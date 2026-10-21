import sys
from collections import deque


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    k = int(data[1])
    p = int(data[2])

    a = list(map(int, data[3:3 + n]))

    if len(data) > 3 + n:
        operations = b"".join(data[3 + n:]).decode()
    else:
        operations = ""

    if len(operations) > p:
        operations = operations[:p]

    total_ones = sum(a)

    if k >= n:
        answers = [str(total_ones) for op in operations if op == '?']
        sys.stdout.write("\n".join(answers))
        if answers:
            sys.stdout.write("\n")
        return

    length = k
    window_count = n - length + 1

    doubled = a + a

    prefix = [0] * (2 * n + 1)
    for i in range(2 * n):
        prefix[i + 1] = prefix[i] + doubled[i]

    sums_count = 2 * n - length
    window_sums = [0] * sums_count

    for i in range(sums_count):
        window_sums[i] = prefix[i + length] - prefix[i]

    best = [0] * n
    dq = deque()

    for i, value in enumerate(window_sums):
        left = i - window_count + 1

        while dq and dq[0] < left:
            dq.popleft()

        while dq and window_sums[dq[-1]] <= value:
            dq.pop()

        dq.append(i)

        if 0 <= left < n:
            best[left] = window_sums[dq[0]]

    start = 0
    answers = []

    for op in operations:
        if op == '?':
            answers.append(str(best[start]))
        else:  # op == '!'
            start -= 1
            if start < 0:
                start = n - 1

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()