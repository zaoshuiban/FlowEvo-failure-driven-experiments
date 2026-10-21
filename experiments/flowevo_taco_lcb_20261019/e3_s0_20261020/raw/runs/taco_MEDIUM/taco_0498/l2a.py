import sys


def read_ints():
    data = sys.stdin.buffer.read()
    num = 0
    in_num = False

    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            in_num = True
        else:
            if in_num:
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

        A = [0] * n
        for i in range(n):
            A[i] = next(it)

        total_b = 0
        current_diff = 0
        max_prefix_diff = 0

        for i in range(n):
            b = next(it)
            total_b += b
            current_diff += A[i] - b
            if current_diff > max_prefix_diff:
                max_prefix_diff = current_diff

        answers.append(str(total_b + max_prefix_diff))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()