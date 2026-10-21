import sys
from bisect import bisect_left


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    ptr = 0
    T = int(data[ptr])
    ptr += 1

    answers = []
    ZERO = ord('0')

    for _ in range(T):
        N = int(data[ptr])
        K = int(data[ptr + 1])
        Q = int(data[ptr + 2])
        ptr += 3

        S = data[ptr]
        ptr += 1

        # a[l] = maximum r such that S[l..r] has at most K zeroes and K ones.
        a = [0] * (N + 1)
        cnt0 = cnt1 = 0
        r = 0

        for l in range(1, N + 1):
            while r < N:
                if S[r] == ZERO:
                    if cnt0 < K:
                        cnt0 += 1
                        r += 1
                    else:
                        break
                else:
                    if cnt1 < K:
                        cnt1 += 1
                        r += 1
                    else:
                        break

            a[l] = r

            if l <= r:
                if S[l - 1] == ZERO:
                    cnt0 -= 1
                else:
                    cnt1 -= 1

        prefix_a = [0] * (N + 1)
        for i in range(1, N + 1):
            prefix_a[i] = prefix_a[i - 1] + a[i]

        for _ in range(Q):
            L = int(data[ptr])
            R = int(data[ptr + 1])
            ptr += 2

            # First index i in [L, R] with a[i] >= R.
            pos = bisect_left(a, R, L, R + 1)

            ans = 0

            # For i in [L, pos - 1], valid endpoints are i..a[i].
            if pos > L:
                cnt = pos - L
                sum_a = prefix_a[pos - 1] - prefix_a[L - 1]
                sum_i = (L + pos - 1) * cnt // 2
                ans += sum_a - sum_i + cnt

            # For i in [pos, R], valid endpoints are i..R.
            if pos <= R:
                cnt = R - pos + 1
                sum_i = (pos + R) * cnt // 2
                ans += cnt * (R + 1) - sum_i

            answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()