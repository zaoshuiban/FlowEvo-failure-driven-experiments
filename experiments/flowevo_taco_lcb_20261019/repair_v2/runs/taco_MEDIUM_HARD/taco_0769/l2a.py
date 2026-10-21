import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    pos = 1
    answers = []

    for _ in range(t):
        n = data[pos]
        pos += 1

        a = data[pos:pos + n]
        pos += n

        total = 0

        for left in range(n - 2):
            a_left = a[left]
            mid = left + 1

            for right in range(left + 2, n):
                a_right = a[right]

                while mid + 1 < right:
                    current = (a[mid] - a_left) * (a_right - a[mid])
                    nxt = (a[mid + 1] - a_left) * (a_right - a[mid + 1])

                    if nxt >= current:
                        mid += 1
                    else:
                        break

                total += (a[mid] - a_left) * (a_right - a[mid])

        answers.append(str(total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()