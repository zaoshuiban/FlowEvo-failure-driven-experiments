import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        k = data[idx + 2]
        idx += 3

        total_weight = 0

        for p in data[idx:idx + k]:
            zero_based = p - 1
            row = zero_based // m + 1
            col = zero_based % m + 1

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