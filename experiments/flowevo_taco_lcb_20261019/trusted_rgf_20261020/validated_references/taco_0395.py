import sys

sys.setrecursionlimit(1_000_000)


def factor(x):
    e2 = e3 = e5 = 0
    while x % 2 == 0:
        e2 += 1
        x //= 2
    while x % 3 == 0:
        e3 += 1
        x //= 3
    while x % 5 == 0:
        e5 += 1
        x //= 5
    return e2, e3, e5, x


class SegTree:
    __slots__ = ("n", "mx", "mn", "lz")

    def __init__(self, arr):
        n = len(arr)
        self.n = n
        size = 4 * n + 5
        self.mx = [0] * size
        self.mn = [0] * size
        self.lz = [0] * size
        self._build(1, 0, n - 1, arr)

    def _build(self, idx, left, right, arr):
        if left == right:
            v = arr[left]
            self.mx[idx] = v
            self.mn[idx] = v
            return

        mid = (left + right) >> 1
        li = idx << 1
        ri = li | 1

        self._build(li, left, mid, arr)
        self._build(ri, mid + 1, right, arr)

        self.mx[idx] = self.mx[li] if self.mx[li] >= self.mx[ri] else self.mx[ri]
        self.mn[idx] = self.mn[li] if self.mn[li] <= self.mn[ri] else self.mn[ri]

    def range_dec(self, ql, qr):
        self._dec(1, 0, self.n - 1, ql, qr)

    def _dec(self, idx, left, right, ql, qr):
        mx = self.mx
        mn = self.mn
        lz = self.lz

        if qr < left or right < ql or mx[idx] == 0:
            return

        if ql <= left and right <= qr and mn[idx] > 0:
            mx[idx] -= 1
            mn[idx] -= 1
            lz[idx] -= 1
            return

        li = idx << 1
        ri = li | 1

        z = lz[idx]
        if z:
            mx[li] += z
            mn[li] += z
            lz[li] += z

            mx[ri] += z
            mn[ri] += z
            lz[ri] += z

            lz[idx] = 0

        mid = (left + right) >> 1

        if ql <= mid:
            self._dec(li, left, mid, ql, qr)
        if qr > mid:
            self._dec(ri, mid + 1, right, ql, qr)

        mx[idx] = mx[li] if mx[li] >= mx[ri] else mx[ri]
        mn[idx] = mn[li] if mn[li] <= mn[ri] else mn[ri]

    def set_value(self, pos, val):
        self._set(1, 0, self.n - 1, pos, val)

    def _set(self, idx, left, right, pos, val):
        mx = self.mx
        mn = self.mn
        lz = self.lz

        if left == right:
            mx[idx] = val
            mn[idx] = val
            lz[idx] = 0
            return

        li = idx << 1
        ri = li | 1

        z = lz[idx]
        if z:
            mx[li] += z
            mn[li] += z
            lz[li] += z

            mx[ri] += z
            mn[ri] += z
            lz[ri] += z

            lz[idx] = 0

        mid = (left + right) >> 1

        if pos <= mid:
            self._set(li, left, mid, pos, val)
        else:
            self._set(ri, mid + 1, right, pos, val)

        mx[idx] = mx[li] if mx[li] >= mx[ri] else mx[ri]
        mn[idx] = mn[li] if mn[li] <= mn[ri] else mn[ri]

    def collect(self):
        out = [0] * self.n
        self._collect(1, 0, self.n - 1, out)
        return out

    def _collect(self, idx, left, right, out):
        mx = self.mx
        lz = self.lz

        if left == right:
            out[left] = mx[idx]
            return

        li = idx << 1
        ri = li | 1

        z = lz[idx]
        if z:
            mx[li] += z
            lz[li] += z

            mx[ri] += z
            lz[ri] += z

            lz[idx] = 0

        mid = (left + right) >> 1
        self._collect(li, left, mid, out)
        self._collect(ri, mid + 1, right, out)


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    ptr = 0

    n = data[ptr]
    ptr += 1

    arr = data[ptr:ptr + n]
    ptr += n

    m = data[ptr]
    ptr += 1

    e2 = [0] * n
    e3 = [0] * n
    e5 = [0] * n
    base = [0] * n

    for i, x in enumerate(arr):
        a, b, c, rest = factor(x)
        e2[i] = a
        e3[i] = b
        e5[i] = c
        base[i] = rest

    tree2 = SegTree(e2)
    tree3 = SegTree(e3)
    tree5 = SegTree(e5)

    del e2, e3, e5, arr

    for _ in range(m):
        typ = data[ptr]
        ptr += 1

        if typ == 1:
            l = data[ptr] - 1
            r = data[ptr + 1] - 1
            p = data[ptr + 2]
            ptr += 3

            if p == 2:
                tree2.range_dec(l, r)
            elif p == 3:
                tree3.range_dec(l, r)
            else:
                tree5.range_dec(l, r)

        else:
            pos = data[ptr] - 1
            d = data[ptr + 1]
            ptr += 2

            a, b, c, rest = factor(d)

            tree2.set_value(pos, a)
            tree3.set_value(pos, b)
            tree5.set_value(pos, c)
            base[pos] = rest

    final2 = tree2.collect()
    final3 = tree3.collect()
    final5 = tree5.collect()

    pow2 = [1] * 64
    pow3 = [1] * 40
    pow5 = [1] * 30

    for i in range(1, 64):
        pow2[i] = pow2[i - 1] * 2
    for i in range(1, 40):
        pow3[i] = pow3[i - 1] * 3
    for i in range(1, 30):
        pow5[i] = pow5[i - 1] * 5

    ans = [None] * n
    for i in range(n):
        value = base[i] * pow2[final2[i]] * pow3[final3[i]] * pow5[final5[i]]
        ans[i] = str(value)

    sys.stdout.write(" ".join(ans))


if __name__ == "__main__":
    main()