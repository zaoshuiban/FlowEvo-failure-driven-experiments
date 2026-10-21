import sys
from bisect import bisect_left


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    try:
        T = int(next(it))
    except StopIteration:
        return

    answers = []

    for _ in range(T):
        N = int(next(it))
        K = int(next(it))
        Q = int(next(it))
        S = next(it)

        # a[i] = maximum right endpoint j such that S[i..j]
        # contains at most K zeroes and at most K ones.
        a = [0] * (N + 1)
        count = [0, 0]
        r = 0

        for l in range(1, N + 1):
            while r < N:
                ch = S[r] - ord('0')
                if count[ch] < K:
                    count[ch] += 1
                    r += 1
                else:
                    break

            a[l] = r

            if l <= r:
                ch = S[l - 1] - ord('0')
                count[ch] -= 1

        prefix_a = [0] * (N + 1)
        for i in range(1, N + 1):
            prefix_a[i] = prefix_a[i - 1] + a[i]

        for _ in range(Q):
            L = int(next(it))
            R = int(next(it))

            # First position in [L, R] with a[pos] >= R.
            pos = bisect_left(a, R, L, R + 1)

            ans = 0

            # For i in [L, pos - 1]: contribution = a[i] - i + 1
            if pos > L:
                cnt = pos - L
                sum_a = prefix_a[pos - 1] - prefix_a[L - 1]
                sum_i = (L + pos - 1) * cnt // 2
                ans += sum_a - sum_i + cnt

            # For i in [pos, R]: contribution = R - i + 1
            if pos <= R:
                cnt = R - pos + 1
                sum_i = (pos + R) * cnt // 2
                ans += cnt * (R + 1) - sum_i

            answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()