import sys

def count_pretty(n: int) -> int:
    if n <= 0:
        return 0

    full_blocks, remainder = divmod(n, 10)
    count = full_blocks * 3

    for digit in (2, 3, 9):
        if digit <= remainder:
            count += 1

    return count


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    index = 1
    answers = []

    for _ in range(t):
        l = data[index]
        r = data[index + 1]
        index += 2

        answers.append(str(count_pretty(r) - count_pretty(l - 1)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()