import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, q = data[0], data[1]
    arr = data[2:2 + n]

    size = 1
    while size < n:
        size <<= 1

    NEG = -10**18
    tree = [NEG] * (2 * size)

    for i, val in enumerate(arr):
        tree[size + i] = val

    for i in range(size - 1, 0, -1):
        tree[i] = max(tree[i << 1], tree[i << 1 | 1])

    idx = 2 + n
    answers = []

    for _ in range(q):
        op = data[idx]
        idx += 1

        if op == 0:
            x = data[idx]
            y = data[idx + 1]
            idx += 2

            pos = size + x - 1
            tree[pos] = y
            pos >>= 1

            while pos:
                tree[pos] = max(tree[pos << 1], tree[pos << 1 | 1])
                pos >>= 1

        else:
            v = data[idx]
            idx += 1

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

            ans = pos - size + 1
            if ans <= n:
                answers.append(str(ans))
            else:
                answers.append("-1")

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()