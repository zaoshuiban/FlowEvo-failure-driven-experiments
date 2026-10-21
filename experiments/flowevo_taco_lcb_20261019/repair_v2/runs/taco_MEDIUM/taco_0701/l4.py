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

    # Any odd n > 1 can be reduced to 1 immediately.
    if n % 2 == 1:
        return True

    # Powers of two greater than 2 are losing.
    if (n & (n - 1)) == 0:
        return False

    # If divisible by 4, divide by its odd part to reach a power of two.
    if n % 4 == 0:
        return True

    # Now n = 2 * odd. It is losing exactly when odd is prime.
    return not is_prime(n // 2)


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        n = int(data[i])
        answers.append("Ashishgup" if ashish_wins(n) else "FastestFinger")

    sys.stdout.write("\n".join(answers) + "\n")


if __name__ == "__main__":
    main()