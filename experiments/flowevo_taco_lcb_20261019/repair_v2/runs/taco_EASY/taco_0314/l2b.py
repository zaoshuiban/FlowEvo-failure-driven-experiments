import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    q = next(it)

    size = 1
    while size < n:
        size <<= 1

    tree = [0] * (2 * size)

    for i in range(n):
        tree[size + i] = next(it)

    for i in range(size - 1, 0, -1):
        tree[i] = max(tree[i << 1], tree[i << 1 | 1])

    answers = []

    for _ in range(q):
        op = next(it)

        if op == 0:
            x = next(it)
            y = next(it)

            pos = size + x - 1
            tree[pos] = y
            pos >>= 1

            while pos:
                tree[pos] = max(tree[pos << 1], tree[pos << 1 | 1])
                pos >>= 1

        else:
            v = next(it)

            if tree[1] < v:
                answers.append("-1")
                continue

            pos = 1
            while pos < size:
                left = pos << 1
                if tree[left] >= v:
                    pos = left
                else:
                    pos = left | 1

            answers.append(str(pos - size + 1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()