import sys

def solve():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        # Number of visited cells is n + m - 1.
        # Its sum can be 0 only if this number is even.
        if (n + m) % 2 == 0:
            for _ in range(n * m):
                next(it)
            answers.append("NO")
            continue

        mn = [0] * m
        mx = [0] * m

        for i in range(n):
            for j in range(m):
                value = next(it)

                if i == 0:
                    if j == 0:
                        mn[j] = mx[j] = value
                    else:
                        current = mn[j - 1] + value
                        mn[j] = mx[j] = current
                else:
                    if j == 0:
                        mn[j] += value
                        mx[j] += value
                    else:
                        min_path = min(mn[j], mn[j - 1]) + value
                        max_path = max(mx[j], mx[j - 1]) + value

                        mn[j] = min_path
                        mx[j] = max_path

        if mn[m - 1] <= 0 <= mx[m - 1]:
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()