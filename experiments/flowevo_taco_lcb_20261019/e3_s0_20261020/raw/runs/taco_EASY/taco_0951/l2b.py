import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        x = data[idx]
        y = data[idx + 1]
        idx += 2

        z = []
        for a, b in zip(x, y):
            if a == b:
                z.append('W' if a == 'B' else 'B')
            else:
                z.append('B')

        answers.append(''.join(z))

    sys.stdout.write('\n'.join(answers))

if __name__ == "__main__":
    solve()