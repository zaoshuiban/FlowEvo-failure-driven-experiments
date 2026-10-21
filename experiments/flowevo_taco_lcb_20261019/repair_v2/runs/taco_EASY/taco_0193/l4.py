import sys


def count_pretty_up_to(n: int) -> int:
    if n <= 0:
        return 0

    full_tens, last_digit = divmod(n, 10)

    # In every complete block of 10 numbers, exactly three are pretty:
    # those ending in 2, 3, and 9.
    ans = full_tens * 3

    if last_digit >= 2:
        ans += 1
    if last_digit >= 3:
        ans += 1
    if last_digit >= 9:
        ans += 1

    return ans


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        l = data[idx]
        r = data[idx + 1]
        idx += 2

        answers.append(str(count_pretty_up_to(r) - count_pretty_up_to(l - 1)))

    sys.stdout.write("\n".join(answers) + "\n")


if __name__ == "__main__":
    main()