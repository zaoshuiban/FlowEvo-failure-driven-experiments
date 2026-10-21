import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _case in range(t):
        n = data[idx]
        idx += 1

        freq = [0] * (n + 2)

        for _i in range(n):
            x = data[idx]
            idx += 1

            while x > n:
                x //= 2

            freq[x] += 1

        possible = True

        for value in range(n, 0, -1):
            if freq[value] == 0:
                possible = False
                break

            extra = freq[value] - 1

            if value > 1:
                freq[value // 2] += extra
            elif extra > 0:
                possible = False
                break

        answers.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()