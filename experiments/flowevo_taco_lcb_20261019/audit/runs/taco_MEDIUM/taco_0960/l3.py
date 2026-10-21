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

        pos = [0] * (n + 1)
        for i in range(n):
            value = data[idx + i]
            pos[value] = i
        idx += n

        ans = 0

        for value in range(1, n):
            if pos[value] > pos[value + 1]:
                required = min(value, n - value)
                if required > ans:
                    ans = required

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()