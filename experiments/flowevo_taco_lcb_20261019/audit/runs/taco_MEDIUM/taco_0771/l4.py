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

        ans = []

        if n % 2 == 1:
            mid = n // 2 + 1
            ans.append(mid)

            m = n // 2
            for i in range(1, m + 1):
                ans.append(i)
                ans.append(n - i + 1)
        else:
            m = n // 2
            mid = m + 1
            ans.append(mid)

            for i in range(1, m):
                ans.append(i)
                ans.append(n - i + 1)

            ans.append(m)

        output.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    solve()