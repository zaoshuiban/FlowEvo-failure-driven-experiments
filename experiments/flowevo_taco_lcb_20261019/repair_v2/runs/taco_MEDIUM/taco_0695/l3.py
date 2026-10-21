import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        idx += 2

        s = data[idx]
        idx += 1

        n = len(s)
        mismatches = 0

        for i in range(n // 2):
            if s[i] != s[n - 1 - i]:
                mismatches += 1

        if mismatches > k:
            answers.append("NO")
        else:
            extra = k - mismatches
            if extra % 2 == 0 or n % 2 == 1:
                answers.append("YES")
            else:
                answers.append("NO")

    sys.stdout.write("\n".join(answers))
    if answers:
        sys.stdout.write("\n")


if __name__ == "__main__":
    solve()