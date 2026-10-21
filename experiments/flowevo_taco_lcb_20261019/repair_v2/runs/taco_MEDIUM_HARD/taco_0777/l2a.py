import sys


def int_generator():
    data = sys.stdin.buffer.read()
    num = 0
    in_number = False

    for b in data:
        if 48 <= b <= 57:
            num = num * 10 + (b - 48)
            in_number = True
        else:
            if in_number:
                yield num
                num = 0
                in_number = False

    if in_number:
        yield num


def solve():
    it = int_generator()

    try:
        T = next(it)
    except StopIteration:
        return

    answers = []

    for _ in range(T):
        N = next(it)
        H = next(it)

        diff = [0] * (N + 1)

        for _ in range(N):
            l = next(it)
            h = next(it)

            diff[l] += 1
            diff[h + 1] -= 1

        current = 0

        for i in range(N):
            current += diff[i]
            diff[i] = current

        window_sum = 0

        for i in range(H):
            window_sum += diff[i]

        best = window_sum

        for i in range(H, N):
            window_sum += diff[i] - diff[i - H]
            if window_sum > best:
                best = window_sum

        answers.append(str(N * H - best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()