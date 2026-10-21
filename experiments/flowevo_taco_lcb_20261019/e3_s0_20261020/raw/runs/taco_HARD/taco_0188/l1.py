import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)
        a = [next(it) for _ in range(n)]

        if k not in a:
            answers.append("no")
            continue

        if n == 1:
            answers.append("yes")
            continue

        possible = False

        for i in range(n):
            if a[i] >= k:
                if i + 1 < n and a[i + 1] >= k:
                    possible = True
                    break
                if i + 2 < n and a[i + 2] >= k:
                    possible = True
                    break

        answers.append("yes" if possible else "no")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()