import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        a = data[idx]
        b = data[idx + 1]
        idx += 2

        # There are b cab drivers, each described by two place numbers.
        idx += 2 * b

        # Minimum edges needed to connect a places is a - 1.
        answers.append(str(a - 1))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()