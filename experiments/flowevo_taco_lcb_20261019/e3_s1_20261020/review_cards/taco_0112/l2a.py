import sys

sys.setrecursionlimit(1 << 20)

def canonical(s):
    n = len(s)
    if n & 1:
        return s

    m = n >> 1
    left = canonical(s[:m])
    right = canonical(s[m:])

    if left <= right:
        return left + right
    return right + left


def main():
    data = sys.stdin.buffer.read().split()
    if len(data) < 2:
        return

    a, b = data[0], data[1]
    n = len(a)

    if n & 1:
        ok = (a == b)
    elif a == b:
        ok = True
    else:
        ok = (canonical(a) == canonical(b))

    sys.stdout.write("YES\n" if ok else "NO\n")


if __name__ == "__main__":
    main()