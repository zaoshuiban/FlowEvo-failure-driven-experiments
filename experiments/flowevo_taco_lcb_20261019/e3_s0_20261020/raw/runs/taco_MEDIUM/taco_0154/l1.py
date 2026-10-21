import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        xs = []
        ys = []

        for _ in range(n):
            x = next(it)
            y = next(it)
            xs.append(x)
            ys.append(y)

        xs.sort()
        ys.sort()

        left = (n - 1) // 2
        right = n // 2

        width = xs[right] - xs[left] + 1
        height = ys[right] - ys[left] + 1

        answers.append(str(width * height))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()