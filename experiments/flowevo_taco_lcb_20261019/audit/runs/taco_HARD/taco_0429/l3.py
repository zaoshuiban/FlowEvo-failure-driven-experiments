import sys
import os


class FastScanner:
    __slots__ = ("data", "idx", "length")

    def __init__(self):
        self.data = b""
        self.idx = 0
        self.length = 0

    def next_int(self):
        data = self.data
        idx = self.idx
        length = self.length

        while True:
            if idx >= length:
                data = os.read(0, 1 << 20)
                length = len(data)
                idx = 0
                if length == 0:
                    self.data = data
                    self.idx = idx
                    self.length = length
                    return 0
            if data[idx] > 32:
                break
            idx += 1

        num = 0
        while True:
            if idx >= length:
                data = os.read(0, 1 << 20)
                length = len(data)
                idx = 0
                if length == 0:
                    break
            c = data[idx]
            if c <= 32:
                break
            num = num * 10 + (c - 48)
            idx += 1

        self.data = data
        self.idx = idx
        self.length = length
        return num


def solve():
    fs = FastScanner()
    t = fs.next_int()
    write = sys.stdout.write

    for _ in range(t):
        n = fs.next_int()
        q = fs.next_int()

        prefs = [None] * n
        totals = [0] * n

        for i in range(n):
            a = fs.next_int()
            pref = [0] * a
            total = 0

            for j in range(a):
                w = fs.next_int()
                total += w
                if j + 1 < a:
                    pref[j + 1] = total

            prefs[i] = pref
            totals[i] = total

        left = [0] * n
        right = [0] * n
        inter = [0] * n

        for i in range(n):
            v1 = fs.next_int() - 1
            v2 = fs.next_int() - 1
            w = fs.next_int()

            right[i] = v1
            inter[i] = w

            nxt = i + 1
            if nxt == n:
                nxt = 0
            left[nxt] = v2

        posL = [0] * n
        posR = [0] * n
        cur = 0

        for i in range(n):
            posL[i] = cur

            pref = prefs[i]
            total = totals[i]

            pL = pref[left[i]]
            pR = pref[right[i]]

            diff = pL - pR
            if diff < 0:
                diff = -diff

            inside = diff
            other = total - diff
            if other < inside:
                inside = other

            cur += inside
            posR[i] = cur
            cur += inter[i]

        cycle_total = cur
        out = []

        for __ in range(q):
            v1 = fs.next_int() - 1
            c1 = fs.next_int() - 1
            v2 = fs.next_int() - 1
            c2 = fs.next_int() - 1

            pref1 = prefs[c1]
            total1 = totals[c1]
            pv1 = pref1[v1]

            p = pref1[left[c1]]
            diff = pv1 - p
            if diff < 0:
                diff = -diff
            dsL = diff
            other = total1 - diff
            if other < dsL:
                dsL = other

            p = pref1[right[c1]]
            diff = pv1 - p
            if diff < 0:
                diff = -diff
            dsR = diff
            other = total1 - diff
            if other < dsR:
                dsR = other

            pref2 = prefs[c2]
            total2 = totals[c2]
            pv2 = pref2[v2]

            p = pref2[left[c2]]
            diff = pv2 - p
            if diff < 0:
                diff = -diff
            ddL = diff
            other = total2 - diff
            if other < ddL:
                ddL = other

            p = pref2[right[c2]]
            diff = pv2 - p
            if diff < 0:
                diff = -diff
            ddR = diff
            other = total2 - diff
            if other < ddR:
                ddR = other

            L1 = posL[c1]
            R1 = posR[c1]
            L2 = posL[c2]
            R2 = posR[c2]

            d = L1 - L2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            best = dsL + d + ddL

            d = L1 - R2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            val = dsL + d + ddR
            if val < best:
                best = val

            d = R1 - L2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            val = dsR + d + ddL
            if val < best:
                best = val

            d = R1 - R2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            val = dsR + d + ddR
            if val < best:
                best = val

            if c1 == c2:
                diff = pv1 - pv2
                if diff < 0:
                    diff = -diff
                direct = diff
                other = total1 - diff
                if other < direct:
                    direct = other
                if direct < best:
                    best = direct

            out.append(str(best))

        if out:
            write("\n".join(out))
            write("\n")


if __name__ == "__main__":
    solve()