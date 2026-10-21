import sys
from math import gcd

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    l, r = map(int, data)
    n = r - l + 1

    if n < 3:
        print(-1)
        return

    for i in range(n):
        a = l + i
        for j in range(i + 1, n):
            b = l + j
            if gcd(a, b) != 1:
                continue

            for k in range(j + 1, n):
                c = l + k
                if gcd(b, c) == 1 and gcd(a, c) != 1:
                    print(a, b, c)
                    return

    print(-1)


if __name__ == "__main__":
    main()