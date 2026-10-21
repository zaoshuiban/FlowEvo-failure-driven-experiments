import sys


def next_lucky(number: str) -> str:
    s = number.lstrip('0') or '0'
    m = len(s)

    # prefix_lucky[i] is True if s[:i] consists only of digits 3 and 5
    prefix_lucky = [True] * (m + 1)
    for i, ch in enumerate(s):
        prefix_lucky[i + 1] = prefix_lucky[i] and (ch == '3' or ch == '5')

    # Try to find the smallest same-length lucky number greater than s
    for i in range(m - 1, -1, -1):
        if not prefix_lucky[i]:
            continue

        ch = s[i]

        if ch < '3':
            digit = '3'
        elif ch < '5':
            digit = '5'
        else:
            continue

        return s[:i] + digit + '3' * (m - i - 1)

    # No same-length lucky number is greater, so use smallest number
    # with one more digit: all 3s.
    return '3' * (m + 1)


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        n = data[i].decode()
        answers.append(next_lucky(n))

    sys.stdout.write('\n'.join(answers))


if __name__ == "__main__":
    main()