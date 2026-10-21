import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        s = data[idx]
        idx += 1
        n = len(s)

        zeros = s.count(b'0')

        if zeros == 0:
            answers.append("0")
            continue

        ones_in_window = 0
        for i in range(zeros):
            if s[i] == 49:  # ord('1')
                ones_in_window += 1

        best = ones_in_window

        for i in range(zeros, n):
            if s[i] == 49:
                ones_in_window += 1
            if s[i - zeros] == 49:
                ones_in_window -= 1

            if ones_in_window < best:
                best = ones_in_window

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()