import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        b = data[idx:idx + n]
        idx += n

        current = sum(b)
        best = current

        for ai, bi in zip(a, b):
            current += ai - bi
            if current > best:
                best = current

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()