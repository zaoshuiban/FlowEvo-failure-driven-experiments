import sys
from collections import deque


def sliding_max_circular(w, size):
    n = len(w)
    doubled = w + w
    dq = deque()
    ans = [0] * n

    for i in range(n + size - 1):
        left = i - size + 1

        while dq and dq[0] < left:
            dq.popleft()

        while dq and doubled[dq[-1]] <= doubled[i]:
            dq.pop()

        dq.append(i)

        if left >= 0:
            ans[left] = doubled[dq[0]]

    return ans


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    k = int(data[1])
    p = int(data[2])

    a = list(map(int, data[3:3 + n]))
    operations = data[3 + n].decode() if 3 + n < len(data) else ""

    total_ones = sum(a)
    output = []

    if k >= n:
        for op in operations:
            if op == '?':
                output.append(str(total_ones))
        sys.stdout.write("\n".join(output))
        return

    window_sums = [0] * n
    current = sum(a[:k])
    window_sums[0] = current

    for i in range(1, n):
        current -= a[i - 1]
        current += a[(i + k - 1) % n]
        window_sums[i] = current

    allowed_count = n - k + 1
    answers = sliding_max_circular(window_sums, allowed_count)

    current_start = 0

    for op in operations:
        if op == '?':
            output.append(str(answers[current_start]))
        else:  # op == '!'
            current_start -= 1
            if current_start < 0:
                current_start = n - 1

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()