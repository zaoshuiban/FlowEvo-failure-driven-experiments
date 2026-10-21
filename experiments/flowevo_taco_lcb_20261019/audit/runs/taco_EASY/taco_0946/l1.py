import sys
import math


def main() -> None:
    l, r = map(int, sys.stdin.readline().split())
    n = r - l + 1

    for i in range(n):
        a = l + i
        for j in range(i + 1, n):
            b = l + j
            if math.gcd(a, b) != 1:
                continue

            for k in range(j + 1, n):
                c = l + k
                if math.gcd(b, c) == 1 and math.gcd(a, c) != 1:
                    print(a, b, c)
                    return

    print(-1)


if __name__ == "__main__":
    main()