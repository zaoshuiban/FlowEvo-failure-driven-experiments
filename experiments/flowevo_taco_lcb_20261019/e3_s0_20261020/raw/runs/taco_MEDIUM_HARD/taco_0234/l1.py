import sys
from random import getrandbits

sys.setrecursionlimit(1_000_000)


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    arr = data[2:2 + n]

    left = [0] * (n + 1)
    right = [0] * (n + 1)
    size = [0] * (n + 1)
    priority = [0] * (n + 1)
    value = [0] * (n + 1)

    def merge(a, b):
        if a == 0:
            return b
        if b == 0:
            return a

        if priority[a] > priority[b]:
            right[a] = merge(right[a], b)
            size[a] = size[left[a]] + size[right[a]] + 1
            return a
        else:
            left[b] = merge(a, left[b])
            size[b] = size[left[b]] + size[right[b]] + 1
            return b

    def split(root, k):
        # Splits into first k elements and the remaining elements.
        if root == 0:
            return 0, 0

        l = left[root]
        if size[l] >= k:
            a, b = split(l, k)
            left[root] = b
            size[root] = size[left[root]] + size[right[root]] + 1
            return a, root
        else:
            a, b = split(right[root], k - size[l] - 1)
            right[root] = a
            size[root] = size[left[root]] + size[right[root]] + 1
            return root, b

    root = 0

    for i in range(1, n + 1):
        value[i] = arr[i - 1]
        size[i] = 1
        priority[i] = getrandbits(64)
        root = merge(root, i)

    idx = 2 + n

    for _ in range(m):
        typ = data[idx]
        i = data[idx + 1]
        j = data[idx + 2]
        idx += 3

        a, bc = split(root, i - 1)
        b, c = split(bc, j - i + 1)

        ac = merge(a, c)

        if typ == 1:
            root = merge(b, ac)
        else:
            root = merge(ac, b)

    result = []
    stack = []
    cur = root

    while stack or cur:
        while cur:
            stack.append(cur)
            cur = left[cur]

        cur = stack.pop()
        result.append(value[cur])
        cur = right[cur]

    answer = abs(result[0] - result[-1])

    sys.stdout.write(str(answer) + "\n")
    sys.stdout.write(" ".join(map(str, result)) + "\n")


if __name__ == "__main__":
    solve()