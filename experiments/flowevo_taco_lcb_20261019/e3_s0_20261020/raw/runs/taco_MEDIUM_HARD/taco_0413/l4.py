import sys


def is_palindrome(s: bytes, left: int, right: int) -> bool:
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True


def can_make_palindrome(s: bytes) -> bool:
    n = len(s)
    left, right = 0, n - 1

    # Skip all already matching outer pairs.
    while left < right and s[left] == s[right]:
        left += 1
        right -= 1

    # The string is already a palindrome.
    # Since n >= 2, deleting a middle character keeps it a palindrome.
    if left >= right:
        return True

    # At the first mismatch, exactly one of these two characters must be deleted.
    if is_palindrome(s, left + 1, right):
        return True
    if is_palindrome(s, left, right - 1):
        return True

    return False


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []
    idx = 1

    for _ in range(t):
        s = data[idx]
        idx += 1
        answers.append("YES" if can_make_palindrome(s) else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()