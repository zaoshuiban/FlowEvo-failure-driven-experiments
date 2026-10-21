import sys
import random


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1
    m = data[idx]
    idx += 1

    A = data[idx:idx + n]
    idx += n

    left = [0] * (n + 1)
    right = [0] * (n + 1)
    size = [0] * (n + 1)
    val = [0] * (n + 1)
    priority = [0] * (n + 1)

    getrandbits = random.getrandbits
    stack = []

    for i in range(1, n + 1):
        val[i] = A[i - 1]
        pr = getrandbits(64)
        priority[i] = pr

        last = 0
        while stack and priority[stack[-1]] < pr:
            last = stack.pop()

        left[i] = last
        if stack:
            right[stack[-1]] = i

        stack.append(i)

    root = stack[0] if stack else 0

    order = []
    st = [root]

    while st:
        u = st.pop()
        order.append(u)
        if left[u]:
            st.append(left[u])
        if right[u]:
            st.append(right[u])

    for u in reversed(order):
        size[u] = size[left[u]] + size[right[u]] + 1

    def split(u, k):
        path = []
        cur = u

        while cur:
            left_size = size[left[cur]]

            if left_size >= k:
                path.append(-cur)
                cur = left[cur]
            else:
                path.append(cur)
                k -= left_size + 1
                cur = right[cur]

        a = 0
        b = 0

        for x in reversed(path):
            if x > 0:
                node = x
                right[node] = a
                size[node] = size[left[node]] + size[right[node]] + 1
                a = node
            else:
                node = -x
                left[node] = b
                size[node] = size[left[node]] + size[right[node]] + 1
                b = node

        return a, b

    def merge(a, b):
        path = []

        while a and b:
            if priority[a] > priority[b]:
                path.append(a)
                a = right[a]
            else:
                path.append(-b)
                b = left[b]

        res = a if a else b

        for x in reversed(path):
            if x > 0:
                node = x
                right[node] = res
                size[node] = size[left[node]] + size[right[node]] + 1
                res = node
            else:
                node = -x
                left[node] = res
                size[node] = size[left[node]] + size[right[node]] + 1
                res = node

        return res

    for _ in range(m):
        typ = data[idx]
        i = data[idx + 1]
        j = data[idx + 2]
        idx += 3

        if typ == 1:
            if i == 1:
                continue

            a, rest = split(root, i - 1)
            b, c = split(rest, j - i + 1)
            root = merge(b, merge(a, c))
        else:
            if j == n:
                continue

            a, rest = split(root, i - 1)
            b, c = split(rest, j - i + 1)
            root = merge(merge(a, c), b)

    result = []
    st = []
    u = root

    while st or u:
        while u:
            st.append(u)
            u = left[u]

        u = st.pop()
        result.append(val[u])
        u = right[u]

    answer = abs(result[0] - result[-1])

    sys.stdout.write(str(answer) + "\n")
    sys.stdout.write(" ".join(map(str, result)) + "\n")


if __name__ == "__main__":
    solve()