import sys


def can_make_palindrome(s: bytes) -> bool:
    n = len(s)
    left, right = 0, n - 1

    # Skip already matching pairs.
    while left < right and s[left] == s[right]:
        left += 1
        right -= 1

    # The original string is already a palindrome.
    # For n >= 2, deleting a middle character always keeps it a palindrome.
    if left >= right:
        return n >= 1

    # First mismatch: we must delete either s[left] or s[right].
    # Try deleting s[left].
    l, r = left + 1, right
    while l < r and s[l] == s[r]:
        l += 1
        r -= 1
    if l >= r:
        return True

    # Try deleting s[right].
    l, r = left, right - 1
    while l < r and s[l] == s[r]:
        l += 1
        r -= 1

    return l >= r


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

    sys.stdout.write("\n".join(answers) + "\n")


if __name__ == "__main__":
    main()