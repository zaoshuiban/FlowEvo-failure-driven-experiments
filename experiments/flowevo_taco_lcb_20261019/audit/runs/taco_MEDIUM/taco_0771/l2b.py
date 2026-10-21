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

        start = n // 2 + 1
        ans = [start]

        low = 1
        high = n

        while len(ans) < n:
            ans.append(low)
            low += 1

            if len(ans) < n:
                ans.append(high)
                high -= 1

        output.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()