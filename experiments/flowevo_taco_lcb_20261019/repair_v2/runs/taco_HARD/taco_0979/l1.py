import sys
from bisect import bisect_right


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        k = int(next(it))
        q = int(next(it))
        s = next(it)

        # e[i] = maximum valid ending position (1-indexed) for a substring
        # starting at i, using at most k zeroes and at most k ones.
        e = [0] * (n + 1)

        right = 0
        cnt0 = 0
        cnt1 = 0

        for left in range(n):
            while right < n:
                ch = s[right]
                if ch == 48:  # '0'
                    if cnt0 + 1 > k:
                        break
                    cnt0 += 1
                else:
                    if cnt1 + 1 > k:
                        break
                    cnt1 += 1
                right += 1

            e[left + 1] = right

            if left < right:
                ch = s[left]
                if ch == 48:
                    cnt0 -= 1
                else:
                    cnt1 -= 1

        pref_e = [0] * (n + 1)
        for i in range(1, n + 1):
            pref_e[i] = pref_e[i - 1] + e[i]

        for _ in range(q):
            L = int(next(it))
            R = int(next(it))

            # Last position p in [L, R] such that e[p] <= R.
            p = bisect_right(e, R, L, R + 1) - 1

            ans = 0

            if p >= L:
                count = p - L + 1
                sum_e = pref_e[p] - pref_e[L - 1]
                sum_i = (L + p) * count // 2
                ans += sum_e - sum_i + count

            if p < R:
                count = R - p
                a = p + 1
                b = R
                sum_i = (a + b) * count // 2
                ans += count * (R + 1) - sum_i

            answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()