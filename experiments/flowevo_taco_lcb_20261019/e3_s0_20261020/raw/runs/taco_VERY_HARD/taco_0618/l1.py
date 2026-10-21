import sys
from bisect import bisect_left, bisect_right


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    ptr = 0
    t = data[ptr]
    ptr += 1

    answers = []
    INF = 10**30

    for _ in range(t):
        n = data[ptr]
        m = data[ptr + 1]
        ptr += 2

        a = data[ptr:ptr + n]
        ptr += n
        a.sort()

        gaps = [[] for _ in range(n - 1)]
        left_req = 0
        right_req = 0

        for _ in range(m):
            l = data[ptr]
            r = data[ptr + 1]
            ptr += 2

            idx = bisect_left(a, l)

            if idx < n and a[idx] <= r:
                continue

            if idx == 0:
                left_req = max(left_req, a[0] - r)
            elif idx == n:
                right_req = max(right_req, l - a[-1])
            else:
                g = idx - 1
                A = a[g]
                B = a[g + 1]
                gaps[g].append((l - A, B - r))

        prev = [(left_req, 0)]

        for g in range(n - 1):
            segs = gaps[g]

            prev.sort(key=lambda x: x[0])

            p = len(prev)
            ys = [0] * p
            pref = [0] * p
            suff = [0] * p

            for i, (y, val) in enumerate(prev):
                ys[i] = y
                cur = val + 2 * y
                if i == 0 or cur < pref[i - 1]:
                    pref[i] = cur
                else:
                    pref[i] = pref[i - 1]

            for i in range(p - 1, -1, -1):
                y, val = prev[i]
                cur = val + y
                if i == p - 1 or cur < suff[i + 1]:
                    suff[i] = cur
                else:
                    suff[i] = suff[i + 1]

            cur_states = []

            if not segs:
                x = 0
                best = INF

                pos_r = bisect_right(ys, x)
                if pos_r > 0:
                    best = x + pref[pos_r - 1]

                pos_l = bisect_left(ys, x)
                if pos_l < p:
                    best = min(best, 2 * x + suff[pos_l])

                cur_states.append((0, best))
            else:
                segs.sort(key=lambda x: x[0])
                s = len(segs)

                suffix_max = [0] * (s + 1)
                for i in range(s - 1, -1, -1):
                    suffix_max[i] = max(suffix_max[i + 1], segs[i][1])

                for k in range(s + 1):
                    x = 0 if k == 0 else segs[k - 1][0]
                    y_next = suffix_max[k]

                    best = INF

                    pos_r = bisect_right(ys, x)
                    if pos_r > 0:
                        best = x + pref[pos_r - 1]

                    pos_l = bisect_left(ys, x)
                    if pos_l < p:
                        best = min(best, 2 * x + suff[pos_l])

                    cur_states.append((y_next, best))

            prev = cur_states

        ans = INF
        x_right = right_req

        for y, val in prev:
            cost = val + x_right + y + min(x_right, y)
            if cost < ans:
                ans = cost

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()