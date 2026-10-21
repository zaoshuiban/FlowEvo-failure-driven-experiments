import sys
import math


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    l, r = map(int, data[:2])
    values = [l + i for i in range(r - l + 1)]
    n = len(values)

    for i in range(n):
        a = values[i]
        for j in range(i + 1, n):
            b = values[j]
            if math.gcd(a, b) != 1:
                continue

            for k in range(j + 1, n):
                c = values[k]
                if math.gcd(b, c) == 1 and math.gcd(a, c) > 1:
                    print(a, b, c)
                    return

    print(-1)


if __name__ == "__main__":
    main()