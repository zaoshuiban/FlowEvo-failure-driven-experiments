import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    out = []

    for i in range(1, t + 1):
        n = int(data[i])
        if n % 8 == 0:
            out.append("Second\n")
        else:
            out.append("First\n")

    sys.stdout.write("".join(out))

if __name__ == "__main__":
    solve()