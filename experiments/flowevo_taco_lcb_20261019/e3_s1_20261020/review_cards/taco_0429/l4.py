import sys


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    answers = []

    for _ in range(t):
        n = next_int()
        q = next_int()

        prefs = [None] * n
        totals = [0] * n

        for i in range(n):
            a = next_int()
            pref = [0] * a
            total = 0

            for j in range(a):
                w = next_int()
                total += w
                if j + 1 < a:
                    pref[j + 1] = total

            prefs[i] = pref
            totals[i] = total

        left = [0] * n
        right = [0] * n
        inter = [0] * n

        for i in range(n):
            v1 = next_int() - 1
            v2 = next_int() - 1
            w = next_int()

            right[i] = v1
            inter[i] = w

            nxt = i + 1
            if nxt == n:
                nxt = 0
            left[nxt] = v2

        pos_left = [0] * n
        pos_right = [0] * n

        cur = 0

        for i in range(n):
            pos_left[i] = cur

            pref = prefs[i]
            total = totals[i]

            p_left = pref[left[i]]
            p_right = pref[right[i]]

            diff = p_left - p_right
            if diff < 0:
                diff = -diff

            inside = diff
            other = total - diff
            if other < inside:
                inside = other

            cur += inside
            pos_right[i] = cur
            cur += inter[i]

        cycle_total = cur

        for _ in range(q):
            v1 = next_int() - 1
            c1 = next_int() - 1
            v2 = next_int() - 1
            c2 = next_int() - 1

            pref1 = prefs[c1]
            total1 = totals[c1]
            pv1 = pref1[v1]

            p = pref1[left[c1]]
            diff = pv1 - p
            if diff < 0:
                diff = -diff
            ds_left = diff
            other = total1 - diff
            if other < ds_left:
                ds_left = other

            p = pref1[right[c1]]
            diff = pv1 - p
            if diff < 0:
                diff = -diff
            ds_right = diff
            other = total1 - diff
            if other < ds_right:
                ds_right = other

            pref2 = prefs[c2]
            total2 = totals[c2]
            pv2 = pref2[v2]

            p = pref2[left[c2]]
            diff = pv2 - p
            if diff < 0:
                diff = -diff
            dt_left = diff
            other = total2 - diff
            if other < dt_left:
                dt_left = other

            p = pref2[right[c2]]
            diff = pv2 - p
            if diff < 0:
                diff = -diff
            dt_right = diff
            other = total2 - diff
            if other < dt_right:
                dt_right = other

            l1 = pos_left[c1]
            r1 = pos_right[c1]
            l2 = pos_left[c2]
            r2 = pos_right[c2]

            best = 10**30

            d = l1 - l2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            best = ds_left + d + dt_left

            d = l1 - r2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            val = ds_left + d + dt_right
            if val < best:
                best = val

            d = r1 - l2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            val = ds_right + d + dt_left
            if val < best:
                best = val

            d = r1 - r2
            if d < 0:
                d = -d
            if cycle_total - d < d:
                d = cycle_total - d
            val = ds_right + d + dt_right
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

            answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()