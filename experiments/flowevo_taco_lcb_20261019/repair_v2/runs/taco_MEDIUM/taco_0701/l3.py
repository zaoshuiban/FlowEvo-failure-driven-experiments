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


def ashish_wins(n: int) -> bool:
    if n == 1:
        return False
    if n == 2:
        return True
    if n % 2 == 1:
        return True

    # n is even
    if (n & (n - 1)) == 0:
        return False

    # n = 2 * p, where p is an odd prime
    if n % 4 == 2 and is_prime(n // 2):
        return False

    return True


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        n = int(data[i])
        answers.append("Ashishgup" if ashish_wins(n) else "FastestFinger")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()