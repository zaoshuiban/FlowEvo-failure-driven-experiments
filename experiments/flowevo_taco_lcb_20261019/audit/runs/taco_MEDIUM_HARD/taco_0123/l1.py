import sys

def is_power_of_two(x: int) -> bool:
    return x > 0 and (x & (x - 1)) == 0

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []

    for i in range(1, t + 1):
        n = data[i]

        if n % 2 == 1:
            if is_power_of_two(n + 1):
                ans.append("Alice")
            else:
                ans.append("Bob")
        else:
            if is_power_of_two(n + 2):
                ans.append("Bob")
            else:
                ans.append("Alice")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()