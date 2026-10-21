import sys
import math

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    limit = math.isqrt(n)
    d = 3
    while d <= limit:
        if n % d == 0:
            return False
        d += 2
    return True

def solve() -> None:
    data = sys.stdin.read().split()
    t = int(data[0])
    ans = []
    idx = 1

    for _ in range(t):
        a = int(data[idx])
        b = int(data[idx + 1])
        idx += 2

        # a^2 - b^2 = (a - b)(a + b)
        # The product is prime only if a - b == 1 and a + b is prime.
        if a - b == 1 and is_prime(a + b):
            ans.append("YES")
        else:
            ans.append("NO")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()