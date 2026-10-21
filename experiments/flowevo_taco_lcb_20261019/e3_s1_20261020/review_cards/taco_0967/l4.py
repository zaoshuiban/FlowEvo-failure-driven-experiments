import sys

def solve():
    data = iter(sys.stdin.buffer.read().split())
    try:
        t = int(next(data))
    except StopIteration:
        return

    answers = []

    for _ in range(t):
        n = int(next(data))
        a = int(next(data))
        b = int(next(data))

        count_a = 0
        count_b = 0

        for _ in range(n):
            x = int(next(data))
            if x == a:
                count_a += 1
            if x == b:
                count_b += 1

        probability = (count_a * count_b) / (n * n)
        answers.append(f"{probability:.10f}")

    sys.stdout.write("\n".join(answers) + "\n")

if __name__ == "__main__":
    solve()