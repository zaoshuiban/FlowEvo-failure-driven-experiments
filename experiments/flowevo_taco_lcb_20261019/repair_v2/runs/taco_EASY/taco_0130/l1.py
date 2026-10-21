import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        if a[0] == min(a):
            ans.append("Bob")
        else:
            ans.append("Alice")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()