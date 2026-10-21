import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    index = 1
    answers = []

    for _ in range(t):
        n = int(data[index])
        starter = data[index + 1]
        index += 2

        score = 0

        for _ in range(n):
            stack = data[index]
            index += 1

            if stack[0] == ord('0'):
                score += stack.count(b'0')
            else:
                score -= stack.count(b'1')

        if score > 0:
            answers.append("Dee")
        elif score < 0:
            answers.append("Dum")
        else:
            if starter == b"Dee":
                answers.append("Dum")
            else:
                answers.append("Dee")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()