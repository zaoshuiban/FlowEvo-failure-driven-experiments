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

        z = bytearray()

        for a, b in zip(x, y):
            cost_b = (a != B) + (b != B)
            cost_w = (a != W) + (b != W)

            if cost_b >= cost_w:
                z.append(B)
            else:
                z.append(W)

        answers.append(z.decode())

    sys.stdout.write('\n'.join(answers))

if __name__ == "__main__":
    solve()