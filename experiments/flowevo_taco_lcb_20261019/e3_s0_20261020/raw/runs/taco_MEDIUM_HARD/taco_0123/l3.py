import sys

def is_power_of_two(x: int) -> bool:
    return x > 0 and (x & (x - 1)) == 0

def solve() -> None:
    it = iter(map(int, sys.stdin.buffer.read().split()))
    try:
        t = next(it)
    except StopIteration:
        return

    ans = []

    for _ in range(t):
        n = next(it)

        if n & 1:  # n is odd
            alice_wins = is_power_of_two(n + 1)
        else:      # n is even
            # Bob wins exactly when n = 2 * (2^k - 1)
            if n % 4 == 2 and is_power_of_two(n // 2 + 1):
                alice_wins = False
            else:
                alice_wins = True

        ans.append("Alice" if alice_wins else "Bob")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()