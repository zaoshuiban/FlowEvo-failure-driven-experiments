import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        a, b, c, d = data[idx:idx + 4]
        idx += 4

        if a > b * c:
            answers.append("-1")
        else:
            m = (c + d - 1) // d
            n = a // (b * d) + 1
            if n > m:
                n = m

            ans = n * a - b * d * n * (n - 1) // 2
            answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()