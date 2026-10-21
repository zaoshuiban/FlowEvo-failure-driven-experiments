import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        if n == 1 or m == 1:
            if n * m == 2:
                ans.append("Yes")
            else:
                ans.append("No")
        else:
            if n % 2 == 0 or m % 2 == 0:
                ans.append("Yes")
            else:
                ans.append("No")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()