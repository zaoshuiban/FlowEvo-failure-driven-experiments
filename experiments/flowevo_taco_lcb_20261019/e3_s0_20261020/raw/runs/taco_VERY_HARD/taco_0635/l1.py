import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    out = []
    idx = 1

    for _ in range(t):
        s = data[idx]
        idx += 1

        n = len(s)
        k = n // 3
        total_n = s.count(b'N')

        # Maximum number of original 'N' characters among positions 1..n-1
        # that can be kept as 'N' without having two adjacent 'N's.
        alpha = 0
        prev_selected = False

        for i in range(n - 1):
            if s[i] == ord('N'):
                if not prev_selected:
                    alpha += 1
                    prev_selected = True
                else:
                    prev_selected = False
            else:
                prev_selected = False

        keep_n = min(k, alpha)
        answer = total_n + k - 2 * keep_n
        out.append(str(answer))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()