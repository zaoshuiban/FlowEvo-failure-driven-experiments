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

        missing_sum = 0
        for _ in range(f):
            missing_sum += next(it)

        torn_leaves = next(it)

        total_printed_sum = n * (n + 1) // 2 - missing_sum
        total_leaves = (n + 1) // 2

        if total_leaves == 0:
            expected = 0.0
        else:
            expected = total_printed_sum * (total_leaves - torn_leaves) / total_leaves

        answers.append(f"{expected + 1e-9:.4f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()