import sys

def count_pretty(n: int) -> int:
    if n <= 0:
        return 0

    q, r = divmod(n, 10)
    ans = q * 3

    if r >= 2:
        ans += 1
    if r >= 3:
        ans += 1
    if r >= 9:
        ans += 1

    return ans


def main():
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

        answers.append(str(count_pretty(r) - count_pretty(l - 1)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()