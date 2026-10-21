import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    B = ord('B')
    W = ord('W')

    for _ in range(t):
        x = data[idx]
        y = data[idx + 1]
        idx += 2

        z = bytearray(b'B' * len(x))

        for i in range(len(x)):
            if x[i] == B and y[i] == B:
                z[i] = W

        answers.append(z.decode())

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()