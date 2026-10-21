import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        m = int(next(it))
        k = int(next(it))

        favorable_sum = 0

        for _ in range(k):
            pos = int(next(it)) - 1
            r = pos // m + 1
            c = pos % m + 1

            row_choices = r * (n - r + 1)
            col_choices = c * (m - c + 1)

            favorable_sum += row_choices * col_choices

        total_rectangles = n * (n + 1) * m * (m + 1) // 4

        answers.append(f"{favorable_sum / total_rectangles:.15f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()