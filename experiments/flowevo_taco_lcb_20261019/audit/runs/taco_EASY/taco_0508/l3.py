import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    ans = []

    for i in range(1, t + 1):
        n = int(data[i])
        ans.append("YES" if n % 4 == 0 else "NO")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()