import sys


def solve():
    data = sys.stdin.buffer.read()
    ndata = len(data)
    idx = 0

    def next_int():
        nonlocal idx
        while idx < ndata and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < ndata and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    answers = []

    for _ in range(t):
        n = next_int()
        h = next_int()

        diff = [0] * (n + 1)

        for _ in range(n):
            l = next_int()
            r = next_int()
            diff[l] += 1
            diff[r + 1] -= 1

        current = 0
        for row in range(n):
            current += diff[row]
            diff[row] = current

        window_sum = 0
        for i in range(h):
            window_sum += diff[i]

        max_empty = window_sum
        limit = n - h

        for start in range(1, limit + 1):
            window_sum += diff[start + h - 1] - diff[start - 1]
            if window_sum > max_empty:
                max_empty = window_sum

        answers.append(str(n * h - max_empty))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()