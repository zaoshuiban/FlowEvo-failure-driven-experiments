import sys

data = sys.stdin.buffer.read()
idx = 0
ndata = len(data)


def next_int():
    global idx
    while idx < ndata and data[idx] <= 32:
        idx += 1
    num = 0
    while idx < ndata and data[idx] > 32:
        num = num * 10 + (data[idx] - 48)
        idx += 1
    return num


def solve():
    ni = next_int
    t = ni()
    answers = []

    for _ in range(t):
        n = ni()
        m = ni()
        k = ni()

        width = m + 1
        pref = [0] * ((n + 1) * width)

        for i in range(1, n + 1):
            base = i * width
            prev = base - width
            row_sum = 0

            for j in range(1, m + 1):
                row_sum += ni()
                pref[base + j] = pref[prev + j] + row_sum

        ans = 0
        p = pref

        for length in range(1, n + 1):
            target = k * length * length
            max_i = n - length
            max_j = m - length

            j = max_j + 1

            for i in range(max_i + 1):
                r1 = i * width
                r2 = (i + length) * width

                while j > 0:
                    c = j - 1
                    c2 = c + length

                    square_sum = (
                        p[r2 + c2]
                        - p[r1 + c2]
                        - p[r2 + c]
                        + p[r1 + c]
                    )

                    if square_sum >= target:
                        j = c
                    else:
                        break

                if j == 0:
                    ans += (max_i - i + 1) * (max_j + 1)
                    break
                elif j <= max_j:
                    ans += max_j - j + 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()