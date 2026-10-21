import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    answers = []

    for _ in range(T):
        N = next(it)
        M = next(it)
        K = next(it)

        total_rectangles = (N * (N + 1) // 2) * (M * (M + 1) // 2)
        numerator = 0

        for _ in range(K):
            x = next(it) - 1
            r, c = divmod(x, M)
            r += 1
            c += 1

            row_choices = r * (N - r + 1)
            col_choices = c * (M - c + 1)
            numerator += row_choices * col_choices

        ans = numerator / total_rectangles
        answers.append(f"{ans:.15f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()