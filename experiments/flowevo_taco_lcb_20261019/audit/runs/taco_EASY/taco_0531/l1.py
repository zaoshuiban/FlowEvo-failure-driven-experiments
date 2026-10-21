import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    ans = []

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        s = data[idx + 2]
        idx += 3

        count = 0
        found = False

        for ch in s:
            if ch == ord('*'):
                count += 1
                if count >= k:
                    found = True
                    break
            else:
                count = 0

        ans.append("YES" if found else "NO")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()