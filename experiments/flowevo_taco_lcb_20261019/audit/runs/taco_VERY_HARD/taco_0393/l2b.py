import sys


def solve():
    data = sys.stdin.buffer.read()
    length = len(data)
    pos = 0

    def next_int():
        nonlocal pos
        while pos < length and data[pos] <= 32:
            pos += 1
        num = 0
        while pos < length and data[pos] > 32:
            num = num * 10 + (data[pos] - 48)
            pos += 1
        return num

    t = next_int()
    output = []

    for _ in range(t):
        n = next_int()
        q = next_int()

        a = [0] * n
        for i in range(n):
            a[i] = next_int()

        m = n - 1
        left_value = [None] * m
        right_value = [None] * m

        for i in range(m):
            u = a[i]
            v = a[i + 1]
            if u <= v:
                left_value[i] = (u, i + 1)
                right_value[i] = (v, i + 1)
            else:
                left_value[i] = (v, i + 1)
                right_value[i] = (u, i + 1)

        del a

        l_arr = [0] * q
        r_arr = [0] * q
        y_arr = [0] * q

        for qi in range(q):
            x1 = next_int()
            x2 = next_int()
            y = next_int()

            l_arr[qi] = x1
            r_arr[qi] = x2 - 1
            y_arr[qi] = y

        left_value.sort()
        right_value.sort()

        order = list(range(q))
        order.sort(key=y_arr.__getitem__)

        bit_low = [0] * (m + 1)
        bit_high = [0] * (m + 1)
        ans = [0] * q

        p1 = 0
        p2 = 0

        for qi in order:
            y = y_arr[qi]

            while p1 < m and left_value[p1][0] <= y:
                idx = left_value[p1][1]
                while idx <= m:
                    bit_low[idx] += 1
                    idx += idx & -idx
                p1 += 1

            while p2 < m and right_value[p2][0] < y:
                idx = right_value[p2][1]
                while idx <= m:
                    bit_high[idx] += 1
                    idx += idx & -idx
                p2 += 1

            l = l_arr[qi]
            r = r_arr[qi]

            count = 0

            idx = r
            while idx > 0:
                count += bit_low[idx]
                idx -= idx & -idx

            idx = l - 1
            while idx > 0:
                count -= bit_low[idx]
                idx -= idx & -idx

            idx = r
            while idx > 0:
                count -= bit_high[idx]
                idx -= idx & -idx

            idx = l - 1
            while idx > 0:
                count += bit_high[idx]
                idx -= idx & -idx

            ans[qi] = count

        output.extend(str(x) for x in ans)

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()