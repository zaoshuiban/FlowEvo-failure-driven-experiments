import sys


def can_make_palindrome(s):
    n = len(s)
    left, right = 0, n - 1

    while left < right and s[left] == s[right]:
        left += 1
        right -= 1

    # The original string is already a palindrome.
    if left >= right:
        return True

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


def main():
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        s = data[i]
        answers.append("YES" if can_make_palindrome(s) else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()