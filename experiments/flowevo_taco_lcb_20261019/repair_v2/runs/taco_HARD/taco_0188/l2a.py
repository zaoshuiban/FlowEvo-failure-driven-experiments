import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        a = data[idx:idx + n]
        idx += n

        if k not in a:
            ans.append("NO")
            continue

        if n == 1:
            ans.append("YES")
            continue

        possible = False

        for i in range(n):
            if a[i] >= k:
                if i + 1 < n and a[i + 1] >= k:
                    possible = True
                    break
                if i + 2 < n and a[i + 2] >= k:
                    possible = True
                    break

        ans.append("YES" if possible else "NO")

    print("\n".join(ans))

if __name__ == "__main__":
    solve()