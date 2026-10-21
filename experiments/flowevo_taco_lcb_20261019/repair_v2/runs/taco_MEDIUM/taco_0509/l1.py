import sys
from math import gcd

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:1 + n]

    ones = a.count(1)
    if ones > 0:
        print(n - ones)
        return

    min_len = n + 1

    for i in range(n):
        g = 0
        for j in range(i, n):
            g = gcd(g, a[j])
            if g == 1:
                min_len = min(min_len, j - i + 1)
                break

    if min_len == n + 1:
        print(-1)
    else:
        print(n + min_len - 2)

if __name__ == "__main__":
    main()