import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    answers = []
    idx = 1

    for _ in range(n):
        i = data[idx]
        j = data[idx + 1]
        idx += 2

        distance = 0
        while i != j:
            if i > j:
                i //= 2
            else:
                j //= 2
            distance += 1

        answers.append(str(distance))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()