import sys

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2

    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])

    ans = []
    idx = 1

    for _ in range(t):
        a = int(data[idx])
        b = int(data[idx + 1])
        idx += 2

        # a^2 - b^2 = (a - b)(a + b)
        if a - b != 1:
            ans.append("NO")
        else:
            ans.append("YES" if is_prime(a + b) else "NO")

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()