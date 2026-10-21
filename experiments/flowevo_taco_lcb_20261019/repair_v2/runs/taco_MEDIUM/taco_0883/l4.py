import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    ans = []

    for _ in range(t):
        n = int(data[idx])
        m = int(data[idx + 1])
        idx += 2

        if n == 1 and m == 1:
            ans.append("No")
        elif n == 1 or m == 1:
            if n * m == 2:
                ans.append("Yes")
            else:
                ans.append("No")
        else:
            if (n & 1) == 0 or (m & 1) == 0:
                ans.append("Yes")
            else:
                ans.append("No")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()