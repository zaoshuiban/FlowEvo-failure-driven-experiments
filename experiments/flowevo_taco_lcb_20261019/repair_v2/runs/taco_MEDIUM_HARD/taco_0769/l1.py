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

        ans = 0

        for left in range(n - 2):
            a = A[left]
            p = left

            for right in range(left + 2, n):
                b = A[right]
                target = a + b

                Ap = A[p]

                while p + 1 <= right:
                    cur = 2 * Ap - target
                    if cur < 0:
                        cur = -cur

                    nxt = 2 * A[p + 1] - target
                    if nxt < 0:
                        nxt = -nxt

                    if nxt <= cur:
                        p += 1
                        Ap = A[p]
                    else:
                        break

                ans += (Ap - a) * (b - Ap)

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()