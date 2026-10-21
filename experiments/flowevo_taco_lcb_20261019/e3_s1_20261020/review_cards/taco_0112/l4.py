import sys


def canonical(s: bytes) -> bytes:
    n = len(s)
    if n & 1:
        return s

    mid = n // 2
    left = canonical(s[:mid])
    right = canonical(s[mid:])

    if left < right:
        return left + right
    return right + left


def main() -> None:
    data = sys.stdin.buffer.read().split()
    s1, s2 = data[0], data[1]

    if s1 == s2:
        print("YES")
        return

    if len(s1) & 1:
        print("NO")
        return

    print("YES" if canonical(s1) == canonical(s2) else "NO")


if __name__ == "__main__":
    main()