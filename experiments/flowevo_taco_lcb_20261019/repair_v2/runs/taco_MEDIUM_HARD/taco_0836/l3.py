import sys


def solve():
    data = sys.stdin.buffer.read()
    idx = 0
    length = len(data)

    def next_int():
        nonlocal idx

        while idx < length and data[idx] <= 32:
            idx += 1

        sign = 1
        if idx < length and data[idx] == 45:  # '-'
            sign = -1
            idx += 1

        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1

        return sign * num

    t = next_int()
    answers = []

    for _ in range(t):
        n = next_int()
        m = next_int()
        k = next_int()

        pref = [[0] * (m + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            prev = pref[i - 1]
            cur = pref[i]
            row_sum = 0

            for j in range(1, m + 1):
                row_sum += next_int()
                cur[j] = row_sum + prev[j]

        ans = 0
        max_size = min(n, m)

        for size in range(1, max_size + 1):
            required_sum = k * size * size
            row_count = n - size + 1
            col_count = m - size + 1

            for top in range(row_count):
                top_pref = pref[top]
                bottom_pref = pref[top + size]

                lo = 0
                hi = col_count

                while lo < hi:
                    mid = (lo + hi) // 2
                    right = mid + size

                    square_sum = (
                        bottom_pref[right]
                        - top_pref[right]
                        - bottom_pref[mid]
                        + top_pref[mid]
                    )

                    if square_sum >= required_sum:
                        hi = mid
                    else:
                        lo = mid + 1

                ans += col_count - lo

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()