import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1
        A = data[idx:idx + n]
        idx += n

        total = 0

        for l in range(n - 2):
            L = A[l]
            p = l + 1

            for r in range(l + 2, n):
                R = A[r]

                while p + 1 < r:
                    ap = A[p]
                    an = A[p + 1]

                    cur = (R - ap) * (ap - L)
                    nxt = (R - an) * (an - L)

                    if nxt >= cur:
                        p += 1
                    else:
                        break

                x = A[p]
                total += (R - x) * (x - L)

        answers.append(str(total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()