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

        count = [0] * (n + 2)

        for _ in range(n):
            x = data[idx]
            idx += 1

            while x > n:
                x //= 2

            count[x] += 1

        possible = True

        for value in range(n, 0, -1):
            if count[value] == 0:
                possible = False
                break

            extra = count[value] - 1

            if value > 1:
                count[value // 2] += extra
            elif extra > 0:
                possible = False
                break

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()