import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        idx += 1
        a = data[idx:idx + n]
        idx += n

        if a[0] > min(a[1:]):
            ans.append("Alice")
        else:
            ans.append("Bob")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()