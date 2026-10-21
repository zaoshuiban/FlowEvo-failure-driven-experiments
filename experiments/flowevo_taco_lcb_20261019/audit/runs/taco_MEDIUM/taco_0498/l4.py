import sys


def ints():
    data = sys.stdin.buffer.read()
    n = len(data)
    i = 0

    while i < n:
        while i < n and data[i] <= 32:
            i += 1

        if i >= n:
            break

        sign = 1
        if data[i] == 45:  # '-'
            sign = -1
            i += 1

        num = 0
        while i < n and 48 <= data[i] <= 57:
            num = num * 10 + (data[i] - 48)
            i += 1

        yield sign * num


def solve():
    it = ints()

    try:
        t = next(it)
    except StopIteration:
        return

    answers = []

    for _ in range(t):
        n = next(it)
        a = [next(it) for _ in range(n)]

        sum_b = 0
        prefix = 0
        max_prefix = 0

        for i in range(n):
            b = next(it)
            sum_b += b
            prefix += a[i] - b

            if prefix > max_prefix:
                max_prefix = prefix

        answers.append(str(sum_b + max_prefix))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()