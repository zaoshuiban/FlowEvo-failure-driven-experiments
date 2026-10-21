import sys
import random


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    pos = 2
    initial = data[pos:pos + n]
    pos += n

    left = [0] * (n + 1)
    right = [0] * (n + 1)
    size = [0] * (n + 1)
    value = [0] * (n + 1)
    priority = [0] * (n + 1)

    sys.setrecursionlimit(1_000_000)

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

    randbits = random.getrandbits

    root = 0
    for i, x in enumerate(initial, 1):
        value[i] = x
        size[i] = 1
        priority[i] = randbits(64)
        root = merge(root, i)

    for _ in range(m):
        typ = data[pos]
        i = data[pos + 1]
        j = data[pos + 2]
        pos += 3

        if (typ == 1 and i == 1) or (typ == 2 and j == n):
            continue

        a, rest = split(root, i - 1)
        b, c = split(rest, j - i + 1)

        if typ == 1:
            root = merge(b, merge(a, c))
        else:
            root = merge(merge(a, c), b)

    result = []
    stack = []
    cur = root

    while cur or stack:
        while cur:
            stack.append(cur)
            cur = left[cur]

        cur = stack.pop()
        result.append(value[cur])
        cur = right[cur]

    ans = abs(result[0] - result[-1])

    sys.stdout.write(str(ans) + "\n")
    sys.stdout.write(" ".join(map(str, result)) + "\n")


if __name__ == "__main__":
    solve()