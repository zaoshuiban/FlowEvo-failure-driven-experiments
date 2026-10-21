import sys


def read_ints():
    data = sys.stdin.buffer.read()
    num = 0
    in_num = False

    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            in_num = True
        elif in_num:
            yield num
            num = 0
            in_num = False

    if in_num:
        yield num


def main():
    it = iter(read_ints())
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        h = next(it)

        diff = [0] * (n + 1)

        for _ in range(n):
            l = next(it)
            r = next(it)
            diff[l] += 1
            diff[r + 1] -= 1

        # Convert difference array into coverage count for each row.
        coverage = 0
        for i in range(n):
            coverage += diff[i]
            diff[i] = coverage

        # Find maximum number of already-empty cells in any height-h window.
        window_sum = 0
        for i in range(h):
            window_sum += diff[i]

        max_empty = window_sum

        for i in range(h, n):
            window_sum += diff[i] - diff[i - h]
            if window_sum > max_empty:
                max_empty = window_sum

        answer = n * h - max_empty
        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()