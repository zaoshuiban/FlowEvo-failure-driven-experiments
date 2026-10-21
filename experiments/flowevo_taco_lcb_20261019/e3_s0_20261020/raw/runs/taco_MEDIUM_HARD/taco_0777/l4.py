import sys
from array import array


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1

        sign = 1
        if idx < length and data[idx] == 45:  # '-'
            sign = -1
            idx += 1

        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1

        return num * sign

    t = next_int()
    answers = []

    for _ in range(t):
        n = next_int()
        H = next_int()

        # Difference array for the number of initial empty cells per row.
        diff = array('i', [0]) * (n + 1)

        for _ in range(n):
            l = next_int()
            r = next_int()
            diff[l] += 1
            diff[r + 1] -= 1

        # Convert difference array to row coverage counts.
        current = 0
        for i in range(n):
            current += diff[i]
            diff[i] = current

        # Maximum total existing empty cells in any H consecutive rows.
        window_sum = 0
        for i in range(H):
            window_sum += diff[i]

        max_overlap = window_sum
        limit = n - H

        for start in range(1, limit + 1):
            window_sum += diff[start + H - 1] - diff[start - 1]
            if window_sum > max_overlap:
                max_overlap = window_sum

        required_cells = n * H
        answers.append(str(required_cells - max_overlap))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()