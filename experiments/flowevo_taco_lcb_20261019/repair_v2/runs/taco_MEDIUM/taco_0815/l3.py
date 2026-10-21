import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        a = int(data[idx])
        b = int(data[idx + 1])
        idx += 2

        if a <= b:
            probability = 0.0
        else:
            probability = (a - b) / (a + b)

        answers.append(f"{probability:.12f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()