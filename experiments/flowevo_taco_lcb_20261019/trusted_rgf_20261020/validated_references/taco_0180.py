import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        a = data[idx]
        b = data[idx + 1]
        idx += 2

        if a % 2 == 0 or b % 2 == 0:
            ans.append("Tuzik")
        else:
            ans.append("Vanka")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()