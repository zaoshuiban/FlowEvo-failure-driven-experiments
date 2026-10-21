import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    out = []
    idx = 1

    for _ in range(t):
        n = int(data[idx])
        m = int(data[idx + 1])
        idx += 2

        if (n == 1 and m == 2) or (n == 2 and m == 1):
            out.append("Yes")
        elif n >= 2 and m >= 2 and ((n & 1) == 0 or (m & 1) == 0):
            out.append("Yes")
        else:
            out.append("No")

    sys.stdout.write("\n".join(out))

if __name__ == "__main__":
    solve()