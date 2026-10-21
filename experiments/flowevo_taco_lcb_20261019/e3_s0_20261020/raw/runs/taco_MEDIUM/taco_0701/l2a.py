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

    # n is even
    if (n & (n - 1)) == 0:
        return "FastestFinger"

    if n % 4 == 0:
        return "Ashishgup"

    # n % 4 == 2, so n = 2 * odd
    odd_part = n // 2
    if is_prime(odd_part):
        return "FastestFinger"
    else:
        return "Ashishgup"


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    answers = [winner(n) for n in data[1:t + 1]]
    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()