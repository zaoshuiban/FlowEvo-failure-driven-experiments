import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    ans = []

    for i in range(1, t + 1):
        n = int(data[i])
        if n % 8 == 0:
            ans.append("Second")
        else:
            ans.append("First")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()