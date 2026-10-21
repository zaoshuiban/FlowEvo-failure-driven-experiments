import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    ans = []

    for _ in range(t):
        n = next(it)
        x = next(it)

        degree = [0] * (n + 1)

        for _ in range(n - 1):
            u = next(it)
            v = next(it)
            degree[u] += 1
            degree[v] += 1

        if degree[x] <= 1 or n % 2 == 0:
            ans.append("Ayush")
        else:
            ans.append("Ashish")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()