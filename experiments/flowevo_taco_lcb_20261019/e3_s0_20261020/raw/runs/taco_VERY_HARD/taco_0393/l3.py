import sys

data = sys.stdin.buffer.read()
ptr = 0


def next_int():
    global ptr
    n = len(data)
    while ptr < n and data[ptr] <= 32:
        ptr += 1
    num = 0
    while ptr < n and data[ptr] > 32:
        num = num * 10 + (data[ptr] - 48)
        ptr += 1
    return num


def solve():
    if not data:
        return

    t = next_int()
    output = []

    for _ in range(t):
        n = next_int()
        q = next_int()

        m = n - 1
        lows = [None] * m
        highs = [None] * m

        prev = next_int()

        for i in range(1, n):
            cur = next_int()

            if prev <= cur:
                lo = prev
                hi = cur
            else:
                lo = cur
                hi = prev

            pos = i
            lows[i - 1] = (lo, pos)
            highs[i - 1] = (hi, pos)

            prev = cur

        queries = [None] * q

        for qi in range(q):
            x1 = next_int()
            x2 = next_int()
            y = next_int()
            queries[qi] = (y, x1, x2 - 1, qi)

        lows.sort()
        highs.sort()
        queries.sort()

        bit_low = [0] * (m + 1)
        bit_high = [0] * (m + 1)
        ans = [0] * q

        p1 = 0
        p2 = 0

        for y, left, right, qi in queries:
            while p1 < m and lows[p1][0] <= y:
                idx = lows[p1][1]
                while idx <= m:
                    bit_low[idx] += 1
                    idx += idx & -idx
                p1 += 1

            while p2 < m and highs[p2][0] < y:
                idx = highs[p2][1]
                while idx <= m:
                    bit_high[idx] += 1
                    idx += idx & -idx
                p2 += 1

            count = 0

            idx = right
            while idx > 0:
                count += bit_low[idx]
                idx -= idx & -idx

            idx = left - 1
            while idx > 0:
                count -= bit_low[idx]
                idx -= idx & -idx

            idx = right
            while idx > 0:
                count -= bit_high[idx]
                idx -= idx & -idx

            idx = left - 1
            while idx > 0:
                count += bit_high[idx]
                idx -= idx & -idx

            ans[qi] = count

        output.extend(str(x) for x in ans)

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()