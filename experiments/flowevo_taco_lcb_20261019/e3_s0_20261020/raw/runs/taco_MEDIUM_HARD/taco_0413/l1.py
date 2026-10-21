import sys


def is_palindrome(s, left, right):
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True


def can_make_palindrome(s):
    left = 0
    right = len(s) - 1

    while left < right and s[left] == s[right]:
        left += 1
        right -= 1

    # Already a palindrome: delete the middle character (or one middle character)
    if left >= right:
        return True

    return (
        is_palindrome(s, left + 1, right)
        or is_palindrome(s, left, right - 1)
    )


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        s = data[i]
        answers.append("YES" if can_make_palindrome(s) else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()