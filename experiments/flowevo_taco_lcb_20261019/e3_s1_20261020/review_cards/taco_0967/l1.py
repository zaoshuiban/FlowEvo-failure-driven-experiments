import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        a = next(it)
        b = next(it)

        count = [0] * (n + 1)
        for _ in range(n):
            count[next(it)] += 1

        probability = (count[a] * count[b]) / (n * n)
        answers.append(f"{probability:.10f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()