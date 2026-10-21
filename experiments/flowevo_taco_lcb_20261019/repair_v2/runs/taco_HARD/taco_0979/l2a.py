import sys
from bisect import bisect_left

def main():
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    T = int(next(it))
    output = []

    for _ in range(T):
        n = int(next(it))
        k = int(next(it))
        q = int(next(it))

        s = next(it)

        leftmost = [0] * (n + 1)

        left = 1
        zeros = 0
        ones = 0

        for right in range(1, n + 1):
            if s[right - 1] == 48:  # '0'
                zeros += 1
            else:
                ones += 1

            while zeros > k or ones > k:
                if s[left - 1] == 48:
                    zeros -= 1
                else:
                    ones -= 1
                left += 1

            leftmost[right] = left

        prefix = [0] * (n + 1)
        total = 0
        for i in range(1, n + 1):
            total += leftmost[i]
            prefix[i] = total

        for __ in range(q):
            L = int(next(it))
            R = int(next(it))

            # Last index t such that leftmost[t] < L
            pos = bisect_left(leftmost, L, 1, n + 1)
            t = pos - 1

            low_end = min(R, t)
            low_count = low_end - L + 1
            if low_count < 0:
                low_count = 0

            high_start = max(L, t + 1)
            if high_start <= R:
                high_sum = prefix[R] - prefix[high_start - 1]
            else:
                high_sum = 0

            sum_max = L * low_count + high_sum

            length = R - L + 1
            sum_r_plus_one = (L + R + 2) * length // 2

            answer = sum_r_plus_one - sum_max
            output.append(str(answer))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()