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

        if (a & 1) and (b & 1):
            ans.append("Vanka")
        else:
            ans.append("Tuzik")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()