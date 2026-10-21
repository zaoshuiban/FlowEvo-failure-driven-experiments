import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        idx += 1

        enemy = bytearray(data[idx])
        idx += 1

        gregor = data[idx]
        idx += 1

        ans = 0

        for i in range(n):
            if gregor[i] != ord('1'):
                continue

            if i > 0 and enemy[i - 1] == ord('1'):
                ans += 1
                enemy[i - 1] = ord('0')
            elif enemy[i] == ord('0'):
                ans += 1
            elif i + 1 < n and enemy[i + 1] == ord('1'):
                ans += 1
                enemy[i + 1] = ord('0')

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()