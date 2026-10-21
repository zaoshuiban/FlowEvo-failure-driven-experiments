import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    q = int(data[1])
    root = (n + 1) // 2

    idx = 2
    answers = []

    for _ in range(q):
        u = int(data[idx])
        s = data[idx + 1]
        idx += 2

        for c in s:
            if c == ord('L'):
                lowbit = u & -u
                if lowbit > 1:
                    u -= lowbit >> 1
            elif c == ord('R'):
                lowbit = u & -u
                if lowbit > 1:
                    u += lowbit >> 1
            else:  # 'U'
                if u != root:
                    lowbit = u & -u
                    if u & (lowbit << 1):
                        u -= lowbit
                    else:
                        u += lowbit

        answers.append(str(u))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()