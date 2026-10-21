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

    if (n & (n - 1)) == 0:
        return False

    half = n // 2
    if half % 2 == 1 and is_prime(half):
        return False

    return True

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []

    for n in data[1:t + 1]:
        ans.append("Ashishgup" if ashish_wins(n) else "FastestFinger")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()