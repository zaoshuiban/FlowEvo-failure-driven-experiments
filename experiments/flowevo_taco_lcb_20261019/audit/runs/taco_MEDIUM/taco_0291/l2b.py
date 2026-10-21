import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)

        f = next(it)
        unreadable_sum = 0
        for _ in range(f):
            unreadable_sum += next(it)

        torn = next(it)

        total_printed_sum = n * (n + 1) // 2 - unreadable_sum
        leaves = (n + 1) // 2  # ceil(n / 2)

        if leaves == 0:
            expected_sum = 0.0
        else:
            expected_sum = total_printed_sum * (leaves - torn) / leaves

        answers.append(f"{expected_sum:.4f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()