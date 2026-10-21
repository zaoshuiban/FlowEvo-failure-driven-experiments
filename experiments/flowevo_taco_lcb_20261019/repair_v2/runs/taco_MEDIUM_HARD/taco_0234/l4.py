import sys
import random

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    sys.setrecursionlimit(1_000_000)

    n, m = data[0], data[1]

    left = [0] * (n + 1)
    right = [0] * (n + 1)
    size = [0] * (n + 1)
    value = [0] * (n + 1)
    priority = [0] * (n + 1)

    for idx in range(1, n + 1):
        value[idx] = data[idx + 1]
        size[idx] = 1
        priority[idx] = random.getrandbits(64) + 1

    def merge(a, b):
        if not a or not b:
            return a or b

        if priority[a] > priority[b]:
            right[a] = merge(right[a], b)
            size[a] = size[left[a]] + size[right[a]] + 1
            return a
        else:
            left[b] = merge(a, left[b])
            size[b] = size[left[b]] + size[right[b]] + 1
            return b

    def split(t, k):
        """
        Split tree t into two trees:
        first contains first k elements, second contains the rest.
        """
        if not t:
            return 0, 0

        if size[left[t]] >= k:
            a, b = split(left[t], k)
            left[t] = b
            size[t] = size[left[t]] + size[right[t]] + 1
            return a, t
        else:
            a, b = split(right[t], k - size[left[t]] - 1)
            right[t] = a
            size[t] = size[left[t]] + size[right[t]] + 1
            return t, b

    root = 0
    for idx in range(1, n + 1):
        root = merge(root, idx)

    ptr = 2 + n

    for _ in range(m):
        typ = data[ptr]
        i = data[ptr + 1]
        j = data[ptr + 2]
        ptr += 3

        prefix, rest = split(root, i - 1)
        middle, suffix = split(rest, j - i + 1)

        if typ == 1:
            root = merge(middle, merge(prefix, suffix))
        else:
            root = merge(merge(prefix, suffix), middle)

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

    out = [str(answer), "\n", " ".join(map(str, result)), "\n"]
    sys.stdout.write("".join(out))


if __name__ == "__main__":
    main()