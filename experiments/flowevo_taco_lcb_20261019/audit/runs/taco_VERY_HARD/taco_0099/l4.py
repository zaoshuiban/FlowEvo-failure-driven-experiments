import sys
from array import array


def int_stream():
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


def main() -> None:
    it = int_stream()

    try:
        n = next(it)
    except StopIteration:
        return

    m = next(it)

    a = array('q')
    append_a = a.append
    for _ in range(n):
        append_a(next(it))

    gaps = array('q', [0]) * n
    for i in range(1, n):
        gaps[i - 1] = a[i] - a[i - 1]
    gaps[n - 1] = a[0] + m - a[n - 1]

    pi = array('q', [0]) * n
    j = 0

    for i in range(1, n):
        value = gaps[i]

        while j > 0 and value != gaps[j]:
            j = pi[j - 1]

        if value == gaps[j]:
            j += 1

        pi[i] = j

    answer = []
    j = 0
    total_len = 2 * n - 1
    last = n - 1
    a0 = a[0]

    for idx in range(total_len):
        value = gaps[last - (idx % n)]

        while j > 0 and value != gaps[j]:
            j = pi[j - 1]

        if value == gaps[j]:
            j += 1

        if j == n:
            start = idx - n + 1
            k = (-start) % n
            answer.append((a0 + a[k]) % m)
            j = pi[n - 1]

    answer.sort()

    if answer:
        sys.stdout.write(str(len(answer)) + "\n")
        sys.stdout.write(" ".join(map(str, answer)) + "\n")
    else:
        sys.stdout.write("0\n")


if __name__ == "__main__":
    main()