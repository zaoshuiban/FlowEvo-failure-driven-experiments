import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        mid = n // 2 + 1
        ans = []
        used = set()

        def add(value):
            if 1 <= value <= n and value not in used:
                used.add(value)
                ans.append(value)

        add(mid)

        low, high = 1, n
        while len(ans) < n:
            add(low)
            low += 1

            add(high)
            high -= 1

        output.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    solve()