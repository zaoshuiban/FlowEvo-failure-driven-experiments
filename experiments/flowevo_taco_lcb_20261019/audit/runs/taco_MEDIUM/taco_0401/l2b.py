import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        positive = []
        ans = 0

        for _ in range(n):
            x = next(it)
            if x == 0:
                ans += 1
            else:
                positive.append(x)

        capacity = n - 1
        positive.sort()

        total = 0
        for x in positive:
            if total + x <= capacity:
                total += x
                ans += 1
            else:
                break

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()