import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        a = data[idx]
        b = data[idx + 1]
        idx += 2

        # Losing positions are exactly those where both stacks have odd size.
        if (a % 2 == 1) and (b % 2 == 1):
            ans.append("Vanka")
        else:
            ans.append("Tuzik")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()