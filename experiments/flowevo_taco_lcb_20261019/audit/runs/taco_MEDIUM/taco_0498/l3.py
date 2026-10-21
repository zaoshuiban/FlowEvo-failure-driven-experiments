import sys


def int_stream():
    data = sys.stdin.buffer.read()
    num = 0
    in_number = False

    for c in data:
        if 48 <= c <= 57:
            num = num * 10 + (c - 48)
            in_number = True
        else:
            if in_number:
                yield num
                num = 0
                in_number = False

    if in_number:
        yield num


def solve():
    it = int_stream()

    try:
        t = next(it)
    except StopIteration:
        return

    answers = []

    for _ in range(t):
        n = next(it)

        a = [next(it) for _ in range(n)]
        b = [next(it) for _ in range(n)]

        # Move before day 1: earn B on all days.
        current = sum(b)
        best = current

        # After moving following day i, earn A[1..i] + B[i+1..N].
        for i in range(n):
            current += a[i] - b[i]
            if current > best:
                best = current

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()