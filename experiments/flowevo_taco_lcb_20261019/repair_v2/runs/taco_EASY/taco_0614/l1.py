import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        n = data[idx]
        s = data[idx + 1]
        idx += 2

        if s <= n:
            ans.append(str(s))
        else:
            ans.append(str(2 * n - s))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()