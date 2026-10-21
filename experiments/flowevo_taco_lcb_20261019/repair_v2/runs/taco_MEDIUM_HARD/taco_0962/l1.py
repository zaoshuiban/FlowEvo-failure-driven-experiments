import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    ans = []
    idx = 1

    for _ in range(t):
        s = data[idx]
        idx += 1

        freq = [0] * 26
        for ch in s:
            freq[ch - 97] += 1

        n = len(s)
        odd_count = sum(f & 1 for f in freq)

        if odd_count == 0:
            ans.append("YES")
        elif n >= 3 * odd_count:
            ans.append("YES")
        else:
            ans.append("NO")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()