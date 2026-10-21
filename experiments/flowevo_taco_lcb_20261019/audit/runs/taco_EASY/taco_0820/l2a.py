import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)
    t = next(it)
    ans = []

    for _ in range(t):
        n = next(it)
        k = next(it)
        values = {next(it) for _ in range(n)}

        possible = False
        for x in values:
            if x + k in values:
                possible = True
                break

        ans.append("YES" if possible else "NO")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()