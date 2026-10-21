import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)

        values = set()
        for _ in range(n):
            values.add(next(it))

        possible = False
        for x in values:
            if x - k in values:
                possible = True
                break

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()