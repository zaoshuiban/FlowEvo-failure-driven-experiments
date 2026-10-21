import sys
from bisect import bisect_left


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    T = int(next(it))
    output = []
    ZERO = ord('0')

    for _ in range(T):
        N = int(next(it))
        K = int(next(it))
        Q = int(next(it))
        S = next(it)

        # right[i] = exclusive maximum endpoint such that S[i:right[i]]
        # contains at most K zeroes and at most K ones.
        right = [0] * N
        cnt0 = cnt1 = 0
        r = 0

        for l in range(N):
            while r < N:
                if S[r] == ZERO:
                    if cnt0 == K:
                        break
                    cnt0 += 1
                else:
                    if cnt1 == K:
                        break
                    cnt1 += 1
                r += 1

            right[l] = r

            if l < r:
                if S[l] == ZERO:
                    cnt0 -= 1
                else:
                    cnt1 -= 1

        # Prefix sums of right[].
        prefix = [0] * (N + 1)
        total = 0
        for i, v in enumerate(right):
            total += v
            prefix[i + 1] = total

        for _ in range(Q):
            L = int(next(it)) - 1
            R = int(next(it)) - 1
            target = R + 1

            # First start i in [L, R] with right[i] >= target.
            pos = bisect_left(right, target, L, R + 1)

            ans = 0

            # For starts L ... pos-1: valid endpoints are i ... right[i]-1.
            if pos > L:
                cnt = pos - L
                sum_right = prefix[pos] - prefix[L]
                sum_i = (L + pos - 1) * cnt // 2
                ans += sum_right - sum_i

            # For starts pos ... R: valid endpoints are i ... R.
            if pos <= R:
                cnt = R - pos + 1
                sum_i = (pos + R) * cnt // 2
                ans += cnt * target - sum_i

            output.append(str(ans))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()