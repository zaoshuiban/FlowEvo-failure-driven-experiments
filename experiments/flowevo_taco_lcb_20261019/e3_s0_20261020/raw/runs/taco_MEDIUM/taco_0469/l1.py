import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)

        base = 0
        remainders = []

        for _ in range(n):
            x = next(it)
            base += x // k
            remainders.append(x % k)

        remainders.sort()

        left = 0
        right = n - 1
        extra = 0

        while left < right:
            if remainders[left] + remainders[right] >= k:
                extra += 1
                left += 1
                right -= 1
            else:
                left += 1

        answers.append(str(base + extra))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()