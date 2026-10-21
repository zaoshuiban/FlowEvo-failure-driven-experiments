import sys


def main() -> None:
    data = iter(map(int, sys.stdin.buffer.read().split()))
    try:
        t = next(data)
    except StopIteration:
        return

    answers = []

    for _ in range(t):
        n = next(data)  # rows
        m = next(data)  # columns
        k = next(data)

        total_weight = 0

        for _ in range(k):
            p = next(data) - 1
            row = p // m + 1
            col = p % m + 1

            total_weight += (
                row * (n - row + 1)
                * col * (m - col + 1)
            )

        total_rectangles = (
            (n * (n + 1) // 2)
            * (m * (m + 1) // 2)
        )

        answer = total_weight / total_rectangles
        answers.append(f"{answer:.15f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()