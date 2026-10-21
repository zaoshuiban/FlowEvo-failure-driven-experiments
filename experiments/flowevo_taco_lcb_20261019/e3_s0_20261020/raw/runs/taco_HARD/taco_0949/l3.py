import sys

def solve() -> None:
    data = sys.stdin.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        s = data[idx]
        idx += 1

        n = len(s)
        zeros = s.count('0')

        if zeros == 0:
            answers.append("0")
            continue

        ones = s[:zeros].count('1')
        min_ones = ones

        # Slide a window of length equal to the number of zeroes.
        # Answer = minimum number of ones in any such window.
        for start in range(1, n - zeros + 1):
            if s[start - 1] == '1':
                ones -= 1
            if s[start + zeros - 1] == '1':
                ones += 1
            if ones < min_ones:
                min_ones = ones

        answers.append(str(min_ones))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()