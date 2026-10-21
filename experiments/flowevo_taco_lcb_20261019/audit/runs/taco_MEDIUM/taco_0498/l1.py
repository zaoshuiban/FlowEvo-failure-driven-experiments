import sys

def main():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        a = [next(it) for _ in range(n)]

        total_b = 0
        prefix = 0
        max_prefix = 0

        for i in range(n):
            b = next(it)
            total_b += b
            prefix += a[i] - b
            if prefix > max_prefix:
                max_prefix = prefix

        answers.append(str(total_b + max_prefix))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()