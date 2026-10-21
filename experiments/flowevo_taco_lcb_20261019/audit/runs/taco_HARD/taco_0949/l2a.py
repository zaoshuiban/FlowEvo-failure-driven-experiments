import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    idx = 1

    for _ in range(t):
        s = data[idx]
        idx += 1

        n = len(s)
        zeros = s.count(b'0')

        if zeros == 0:
            out.append("0")
            continue

        ones_in_window = sum(1 for ch in s[:zeros] if ch == ord('1'))
        ans = ones_in_window

        for i in range(zeros, n):
            if s[i] == ord('1'):
                ones_in_window += 1
            if s[i - zeros] == ord('1'):
                ones_in_window -= 1
            if ones_in_window < ans:
                ans = ones_in_window

        out.append(str(ans))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()