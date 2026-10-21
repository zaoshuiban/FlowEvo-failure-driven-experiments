import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]      # rows
        m = data[idx + 1]  # columns
        k = data[idx + 2]
        idx += 3

        total_weight = 0

        for j in range(idx, idx + k):
            p = data[j] - 1
            row = p // m + 1
            col = p % m + 1

            total_weight += (
                row * (n - row + 1)
                * col * (m - col + 1)
            )

        idx += k

        total_rectangles = (
            (n * (n + 1) // 2)
            * (m * (m + 1) // 2)
        )

        answer = total_weight / total_rectangles
        answers.append(f"{answer:.15f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()