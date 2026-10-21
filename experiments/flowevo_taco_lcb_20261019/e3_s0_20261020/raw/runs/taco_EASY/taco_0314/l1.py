import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    q = data[idx + 1]
    idx += 2

    arr = data[idx:idx + n]
    idx += n

    size = 1
    while size < n:
        size <<= 1

    tree = [0] * (2 * size)

    for i, value in enumerate(arr):
        tree[size + i] = value

    for i in range(size - 1, 0, -1):
        tree[i] = max(tree[i << 1], tree[i << 1 | 1])

    answers = []

    for _ in range(q):
        operation_type = data[idx]
        idx += 1

        if operation_type == 0:
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

            node = 1

            while node < size:
                left = node << 1
                if tree[left] >= v:
                    node = left
                else:
                    node = left | 1

            position = node - size

            if position < n:
                answers.append(str(position + 1))
            else:
                answers.append("-1")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()