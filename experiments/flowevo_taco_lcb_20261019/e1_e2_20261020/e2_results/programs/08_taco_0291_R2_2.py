import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        f = data[idx]
        idx += 1

        missing = set()
        for _ in range(f):
            missing.add(data[idx])
            idx += 1

        torn = data[idx]
        idx += 1

        # Total sum of page numbers that are actually printed.
        total_sum = n * (n + 1) // 2
        missing_sum = sum(p for p in missing if 1 <= p <= n)
        printed_sum = total_sum - missing_sum

        # Number of physical leaves in the magazine.
        leaves = (n + 1) // 2

        if leaves == 0:
            expected_sum = 0.0
        else:
            torn = min(max(torn, 0), leaves)
            expected_sum = printed_sum * (leaves - torn) / leaves

        answers.append(f"{expected_sum:.4f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()
