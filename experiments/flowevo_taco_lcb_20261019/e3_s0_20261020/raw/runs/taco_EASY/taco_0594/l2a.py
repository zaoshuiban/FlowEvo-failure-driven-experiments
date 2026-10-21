import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    ans = []
    idx = 1

    for _ in range(t):
        n = int(data[idx])
        idx += 1
        ans.append(" ".join(map(str, range(n, 0, -1))))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()