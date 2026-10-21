import sys

sys.setrecursionlimit(1_000_000)

def canonical(s: bytes) -> bytes:
    n = len(s)
    if n & 1:
        return s

    mid = n // 2
    a = canonical(s[:mid])
    b = canonical(s[mid:])

    if a < b:
        return a + b
    return b + a


def main() -> None:
    data = sys.stdin.buffer.read().split()
    s1, s2 = data[0], data[1]

    if canonical(s1) == canonical(s2):
        print("YES")
    else:
        print("NO")


if __name__ == "__main__":
    main()