import sys

def next_lucky(s: str) -> str:
    n = len(s)

    # valid[i] is True if s[:i] consists only of lucky digits (3 and 5)
    valid = [False] * (n + 1)
    valid[0] = True

    for i, ch in enumerate(s):
        valid[i + 1] = valid[i] and (ch == '3' or ch == '5')

    # Try to construct the smallest lucky number of the same length
    for i in range(n - 1, -1, -1):
        if valid[i]:
            ch = s[i]

            if ch < '3':
                d = '3'
            elif ch < '5':
                d = '5'
            else:
                continue

            return s[:i] + d + '3' * (n - i - 1)

    # If no same-length lucky number is greater, use the smallest of length n + 1
    return '3' * (n + 1)


def main():
    data = sys.stdin.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        answers.append(next_lucky(data[i]))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()