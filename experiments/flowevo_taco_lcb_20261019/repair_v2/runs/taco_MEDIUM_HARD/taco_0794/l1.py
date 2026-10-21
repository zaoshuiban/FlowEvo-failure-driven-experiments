import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:1 + n]
    p = [x - 1 for x in data[1 + n:1 + 2 * n]]

    parent = [-1] * n
    sums = [0] * n
    ans = [0] * (n + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    max_sum = 0

    for j in range(n - 1, -1, -1):
        pos = p[j]

        parent[pos] = pos
        sums[pos] = a[pos]
        if sums[pos] > max_sum:
            max_sum = sums[pos]

        if pos > 0 and parent[pos - 1] != -1:
            r1 = find(pos)
            r2 = find(pos - 1)
            if r1 != r2:
                parent[r2] = r1
                sums[r1] += sums[r2]
                if sums[r1] > max_sum:
                    max_sum = sums[r1]

        if pos + 1 < n and parent[pos + 1] != -1:
            r1 = find(pos)
            r2 = find(pos + 1)
            if r1 != r2:
                parent[r2] = r1
                sums[r1] += sums[r2]
                if sums[r1] > max_sum:
                    max_sum = sums[r1]

        ans[j] = max_sum

    sys.stdout.write("\n".join(str(ans[i]) for i in range(1, n + 1)))


if __name__ == "__main__":
    solve()