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

        lo_events = []
        hi_events = []

        prev = next_int()

        for i in range(1, n):
            cur = next_int()

            if prev <= cur:
                lo = prev
                hi = cur
            else:
                lo = cur
                hi = prev

            lo_events.append((lo, i))
            hi_events.append((hi, i))

            prev = cur

        queries = []

        for qi in range(q):
            x1 = next_int()
            x2 = next_int()
            y = next_int()

            # Segments that can possibly be intersected are x1 ... x2 - 1
            queries.append((y, x1, x2 - 1, qi))

        lo_events.sort()
        hi_events.sort()
        queries.sort()

        bit_lo = [0] * (m + 1)
        bit_hi = [0] * (m + 1)

        ans = [0] * q

        p1 = 0
        p2 = 0

        for y, left, right, qi in queries:
            # Activate segments with min(A[i], A[i+1]) <= y
            while p1 < m and lo_events[p1][0] <= y:
                idx = lo_events[p1][1]
                while idx <= m:
                    bit_lo[idx] += 1
                    idx += idx & -idx
                p1 += 1

            # Activate segments with max(A[i], A[i+1]) < y
            while p2 < m and hi_events[p2][0] < y:
                idx = hi_events[p2][1]
                while idx <= m:
                    bit_hi[idx] += 1
                    idx += idx & -idx
                p2 += 1

            count = 0

            idx = right
            while idx > 0:
                count += bit_lo[idx]
                idx -= idx & -idx

            idx = left - 1
            while idx > 0:
                count -= bit_lo[idx]
                idx -= idx & -idx

            idx = right
            while idx > 0:
                count -= bit_hi[idx]
                idx -= idx & -idx

            idx = left - 1
            while idx > 0:
                count += bit_hi[idx]
                idx -= idx & -idx

            ans[qi] = count

        output.extend(map(str, ans))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()