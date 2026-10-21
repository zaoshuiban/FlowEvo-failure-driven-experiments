import sys

def is_prime(x: int) -> bool:
    if x < 2:
        return False
    if x % 2 == 0:
        return x == 2

    d = 3
    while d * d <= x:
        if x % d == 0:
            return False
        d += 2
    return True


def winner(n: int) -> str:
    if n == 1:
        return "FastestFinger"
    if n == 2:
        return "Ashishgup"
    if n % 2 == 1:
        return "Ashishgup"

    # n is even and greater than 2
    if n & (n - 1) == 0:
        return "FastestFinger"

    if n % 4 == 0:
        return "Ashishgup"

    # n % 4 == 2, so n = 2 * odd
    if is_prime(n // 2):
        return "FastestFinger"

    return "Ashishgup"


def main() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    ans = []

    for i in range(1, t + 1):
        n = int(data[i])
        ans.append(winner(n))

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    main()