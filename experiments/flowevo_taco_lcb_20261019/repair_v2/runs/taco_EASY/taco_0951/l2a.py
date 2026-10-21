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

        z = bytearray(len(x))

        for i in range(len(x)):
            if x[i] == y[i]:
                z[i] = W if x[i] == B else B
            else:
                z[i] = B

        answers.append(bytes(z))

    sys.stdout.buffer.write(b'\n'.join(answers))

if __name__ == "__main__":
    solve()