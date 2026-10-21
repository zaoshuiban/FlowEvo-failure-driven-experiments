import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for case in range(1, t + 1):
        s = data[case]

        last1 = last2 = last3 = -1
        best = len(s) + 1

        for i, ch in enumerate(s):
            if ch == ord('1'):
                last1 = i
            elif ch == ord('2'):
                last2 = i
            else:
                last3 = i

            if last1 != -1 and last2 != -1 and last3 != -1:
                left = last1
                if last2 < left:
                    left = last2
                if last3 < left:
                    left = last3

                current = i - left + 1
                if current < best:
                    best = current

        answers.append(str(best if best != len(s) + 1 else 0))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()