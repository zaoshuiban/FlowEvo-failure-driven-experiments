import sys
from math import isqrt

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2

    limit = isqrt(n)
    d = 3
    while d <= limit:
        if n % d == 0:
            return False
        d += 2
    return True

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        a = data[idx]
        b = data[idx + 1]
        idx += 2

        if a - b == 1 and is_prime(a + b):
            ans.append("YES")
        else:
            ans.append("NO")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()