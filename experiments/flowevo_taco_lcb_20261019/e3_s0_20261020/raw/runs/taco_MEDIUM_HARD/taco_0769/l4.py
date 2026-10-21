import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        total = 0
        last = a[-1]

        for left in range(n - 2):
            minimum = a[left]

            if minimum == last:
                break

            p = left + 1

            for right in range(left + 2, n):
                maximum = a[right]
                target_sum = minimum + maximum

                while p < right and (a[p] << 1) < target_sum:
                    p += 1

                best = 0

                if p < right:
                    x = a[p]
                    if x < maximum:
                        value = (x - minimum) * (maximum - x)
                        if value > best:
                            best = value

                q = p - 1
                if q > left and q < right:
                    x = a[q]
                    if minimum < x < maximum:
                        value = (x - minimum) * (maximum - x)
                        if value > best:
                            best = value

                total += best

        answers.append(str(total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()