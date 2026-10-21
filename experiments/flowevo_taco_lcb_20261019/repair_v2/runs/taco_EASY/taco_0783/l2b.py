import sys

def solve() -> None:
    data = sys.stdin.read().split()
    t = int(data[0])
    answers = []

    for case in range(1, t + 1):
        s = data[case]
        last = [-1, -1, -1]
        ans = len(s) + 1

        for i, ch in enumerate(s):
            last[ord(ch) - ord('1')] = i
            mn = min(last)

            if mn != -1:
                ans = min(ans, i - mn + 1)

        answers.append(str(ans if ans != len(s) + 1 else 0))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()