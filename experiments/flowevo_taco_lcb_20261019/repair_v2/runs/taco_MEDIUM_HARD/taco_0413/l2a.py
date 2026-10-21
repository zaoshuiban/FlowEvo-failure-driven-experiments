import sys


def is_palindrome(s, left, right):
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for idx in range(1, t + 1):
        s = data[idx]
        left, right = 0, len(s) - 1

        while left < right and s[left] == s[right]:
            left += 1
            right -= 1

        if left >= right:
            answers.append("YES")
        else:
            if is_palindrome(s, left + 1, right) or is_palindrome(s, left, right - 1):
                answers.append("YES")
            else:
                answers.append("NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()