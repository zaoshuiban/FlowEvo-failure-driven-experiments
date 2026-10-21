import sys


def next_lucky(s: str) -> str:
    s = s.lstrip('0') or '0'
    n = len(s)

    # pref[i] is True if s[:i] consists only of lucky digits 3 and 5
    pref = [True] * (n + 1)
    for i, ch in enumerate(s):
        pref[i + 1] = pref[i] and ch in "35"

    # Find the rightmost position where we can place a larger lucky digit
    for i in range(n - 1, -1, -1):
        if not pref[i]:
            continue

        for digit in "35":
            if digit > s[i]:
                return s[:i] + digit + "3" * (n - i - 1)

    # No lucky number of the same length is greater, so use the next length
    return "3" * (n + 1)


def main() -> None:
    data = sys.stdin.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for s in data[1:1 + t]:
        answers.append(next_lucky(s))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()