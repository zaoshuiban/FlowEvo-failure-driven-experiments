import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    q = next(it)

    arr = [next(it) for _ in range(n)]

    size = 1
    while size < n:
        size <<= 1

    seg = [0] * (2 * size)

    for i in range(n):
        seg[size + i] = arr[i]

    for i in range(size - 1, 0, -1):
        seg[i] = max(seg[i << 1], seg[i << 1 | 1])

    answers = []

    for _ in range(q):
        op = next(it)

        if op == 0:
            x = next(it)
            y = next(it)

            pos = size + x - 1
            seg[pos] = y
            pos >>= 1

            while pos:
                seg[pos] = max(seg[pos << 1], seg[pos << 1 | 1])
                pos >>= 1

        else:
            v = next(it)

            if seg[1] < v:
                answers.append("-1")
                continue

            pos = 1
            while pos < size:
                left = pos << 1
                if seg[left] >= v:
                    pos = left
                else:
                    pos = left | 1

            answers.append(str(pos - size + 1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()