import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        d = data[idx:idx + n]
        idx += n

        d.sort()

        negative_sum = 0
        for i, value in enumerate(d):
            negative_sum += value * (n - 1 - 2 * i)

        answer = negative_sum + d[-1]
        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()