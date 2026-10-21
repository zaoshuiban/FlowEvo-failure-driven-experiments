import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        x = data[idx + 1]
        s = data[idx + 2]
        idx += 3

        for _ in range(s):
            a = data[idx]
            b = data[idx + 1]
            idx += 2

            if x == a:
                x = b
            elif x == b:
                x = a

        answers.append(str(x))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()