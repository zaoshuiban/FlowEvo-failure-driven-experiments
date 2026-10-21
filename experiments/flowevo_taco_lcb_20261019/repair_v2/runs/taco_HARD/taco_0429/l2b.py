import sys


class FastScanner:
    __slots__ = ("data", "idx", "length")

    def __init__(self):
        self.data = sys.stdin.buffer.read()
        self.idx = 0
        self.length = len(self.data)

    def next_int(self):
        data = self.data
        n = self.length
        i = self.idx

        while i < n and data[i] <= 32:
            i += 1

        sign = 1
        if i < n and data[i] == 45:
            sign = -1
            i += 1

        num = 0
        while i < n and data[i] > 32:
            num = num * 10 + (data[i] - 48)
            i += 1

        self.idx = i
        return num * sign


def solve():
    fs = FastScanner()
    t = fs.next_int()

    answers = []

    for _ in range(t):
        n = fs.next_int()
        q = fs.next_int()

        prefixes = []
        totals = []

        for _ in range(n):
            a = fs.next_int()
            pref = [0] * a
            total = 0

            for j in range(a):
                w = fs.next_int()
                total += w
                if j + 1 < a:
                    pref[j + 1] = total

            prefixes.append(pref)
            totals.append(total)

        left = [0] * (n + 1)
        right = [0] * (n + 1)
        inter_weight = [0] * (n + 1)

        for i in range(1, n + 1):
            v1 = fs.next_int()
            v2 = fs.next_int()
            w = fs.next_int()

            right[i] = v1
            inter_weight[i] = w

            nxt = i % n + 1
            left[nxt] = v2

        pos_left = [0] * (n + 1)
        pos_right = [0] * (n + 1)

        cur = 0

        for i in range(1, n + 1):
            pos_left[i] = cur

            pref = prefixes[i - 1]
            total = totals[i - 1]

            a = pref[left[i] - 1]
            b = pref[right[i] - 1]

            diff = a - b
            if diff < 0:
                diff = -diff

            inside_dist = diff
            other = total - diff
            if other < inside_dist:
                inside_dist = other

            cur += inside_dist
            pos_right[i] = cur
            cur += inter_weight[i]

        cycle_total = cur

        for _ in range(q):
            v1 = fs.next_int()
            c1 = fs.next_int()
            v2 = fs.next_int()
            c2 = fs.next_int()

            pref1 = prefixes[c1 - 1]
            total1 = totals[c1 - 1]
            pv1 = pref1[v1 - 1]

            a = pref1[left[c1] - 1]
            diff = pv1 - a
            if diff < 0:
                diff = -diff
            dist_s_left = diff
            other = total1 - diff
            if other < dist_s_left:
                dist_s_left = other

            b = pref1[right[c1] - 1]
            diff = pv1 - b
            if diff < 0:
                diff = -diff
            dist_s_right = diff
            other = total1 - diff
            if other < dist_s_right:
                dist_s_right = other

            pref2 = prefixes[c2 - 1]
            total2 = totals[c2 - 1]
            pv2 = pref2[v2 - 1]

            a = pref2[left[c2] - 1]
            diff = pv2 - a
            if diff < 0:
                diff = -diff
            dist_d_left = diff
            other = total2 - diff
            if other < dist_d_left:
                dist_d_left = other

            b = pref2[right[c2] - 1]
            diff = pv2 - b
            if diff < 0:
                diff = -diff
            dist_d_right = diff
            other = total2 - diff
            if other < dist_d_right:
                dist_d_right = other

            pL1 = pos_left[c1]
            pR1 = pos_right[c1]
            pL2 = pos_left[c2]
            pR2 = pos_right[c2]

            # Left -> Left
            d = pL1 - pL2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            best = dist_s_left + d + dist_d_left

            # Left -> Right
            d = pL1 - pR2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            val = dist_s_left + d + dist_d_right
            if val < best:
                best = val

            # Right -> Left
            d = pR1 - pL2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            val = dist_s_right + d + dist_d_left
            if val < best:
                best = val

            # Right -> Right
            d = pR1 - pR2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            val = dist_s_right + d + dist_d_right
            if val < best:
                best = val

            answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()