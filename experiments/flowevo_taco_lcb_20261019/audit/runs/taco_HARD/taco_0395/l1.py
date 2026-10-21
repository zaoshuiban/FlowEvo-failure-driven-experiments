```python
import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    ptr = 0
    n = data[ptr]
    ptr += 1

    arr = data[ptr:ptr + n]
    ptr += n

    m = data[ptr]
    ptr += 1

    size = 1
    while size < n:
        size <<= 1

    total_size = size << 1

    mx2 = [0] * total_size
    mn2 = [0] * total_size
    lz2 = [0] * total_size

    mx3 = [0] * total_size
    mn3 = [0] * total_size
    lz3 = [0] * total_size

    mx5 = [0] * total_size
    mn5 = [0] * total_size
    lz5 = [0] * total_size

    base = [0] * n

    for i, val in enumerate(arr):
        x = val

        e2 = 0
        while (x & 1) == 0:
            e2 += 1
            x >>= 1

        e3 = 0
        while x % 3 == 0:
            e3 += 1
            x //= 3

        e5 = 0
        while x % 5 == 0:
            e5 += 1
            x //= 5

        base[i] = x
        pos = size + i

        mx2[pos] = mn2[pos] = e2
        mx3[pos] = mn3[pos] = e3
        mx5[pos] = mn5[pos] = e5

    for node in range(size - 1, 0, -1):
        left = node << 1
        right = left | 1

        mx2[node] = mx2[left] if mx2[left] >= mx2[right] else mx2[right]
        mn2[node] = mn2[left] if mn2[left] <= mn2[right] else mn2[right]

        mx3[node] = mx3[left] if mx3[left] >= mx3[right] else mx3[right]
        mn3[node] = mn3[left] if mn3[left] <= mn3[right] else mn3[right]

        mx5[node] = mx5[left] if mx5[left] >= mx5[right] else mx5[right]
        mn5[node] = mn5[left] if mn5[left] <= mn5[right] else mn5[right]

    def range_dec(mx, mn, lz, ql, qr, node, left, right):
        if qr < left or right < ql or mx[node] == 0:
            return

        if ql <= left and right <= qr and mn[node] > 0:
            mx[node] -= 1
            mn[node] -= 1
            lz[node] += 1
            return

        if left == right:
            return

        z = lz[node]
        lc = node << 1
        rc = lc | 1

        if z:
            mx[lc] -= z
            mn[lc] -= z
            lz[lc] += z

            mx[rc] -= z
            mn[rc] -= z
            lz[rc] += z

            lz[node] = 0

        mid = (left + right) >> 1

        if ql <= mid:
            range_dec(mx, mn, lz, ql, qr, lc, left, mid)

        if qr > mid:
            range_dec(mx, mn, lz, ql, qr, rc, mid + 1, right)

        mx[node] = mx[lc] if mx[lc] >= mx[rc] else mx[rc]
        mn[node] = mn[lc] if mn[lc] <= mn[rc] else mn[rc]

    def point_set(mx, mn, lz, idx, val, node, left, right):
        if left == right:
            mx[node] = val
            mn[node] = val
            lz[node] = 0
            return

        z = lz[node]
        lc = node << 1
        rc = lc | 1

        if z:
            mx[lc] -= z
            mn[lc] -= z
            lz[lc] += z

            mx[rc] -= z
            mn[rc] -= z
            lz[rc] += z

            lz[node] = 0

        mid = (left + right) >> 1

        if idx <= mid:
            point_set(mx, mn, lz, idx, val, lc, left, mid)
        else:
            point_set(mx, mn, lz, idx, val, rc, mid + 1, right)

        mx[node] = mx[lc] if mx[lc] >= mx[rc] else mx[rc]
        mn[node] = mn[lc] if mn[lc] <= mn[rc] else mn[rc]

    def collect(mx, lz, result, node, left, right):
        if left >= n:
            return

        if left == right:
            result[left] = mx[node]
            return

        z = lz[node]
        lc = node << 1
        rc = lc | 1

        if z:
            mx[lc] -= z
            lz[lc] += z

            mx[rc] -= z
            lz[rc] += z

            lz[node] = 0

        mid = (left + right) >> 1

        collect(mx, lz, result, lc, left, mid)

        if mid + 1 < n:
            collect(mx, lz, result, rc, mid + 1, right)

    for _ in range(m):
        typ = data[ptr]
        ptr += 1

        if typ == 1:
            l = data[ptr] - 1
            r = data[ptr + 1] - 1
            p = data[ptr + 2]
            ptr += 3

            if p == 2:
                range_dec(mx2, mn2, lz2, l, r, 1, 0, size - 1)
            elif p == 3:
                range_dec(mx3, mn3, lz3, l, r, 1, 0, size - 1)
            else:
                range_dec(mx5, mn5, lz5, l, r, 1, 0, size - 1)

        else:
            idx = data[ptr] - 1
            d = data[ptr + 1]
            ptr += 2

            x = d

            e2 = 0
            while (x & 1) == 0:
                e2 += 1
                x >>= 1

            e3 = 0
            while x % 3 == 0:
                e3 += 1
                x //= 3

            e5 =