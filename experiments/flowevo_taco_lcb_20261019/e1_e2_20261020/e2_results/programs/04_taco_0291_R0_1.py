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

        unprinted = set()
        for _ in range(f):
            unprinted.add(data[idx])
            idx += 1

        torn = data[idx]
        idx += 1

        total_sum = n * (n + 1) // 2

        removed_sum = 0
        for p in unprinted:
            if 1 <= p <= n:
                removed_sum += p

        remaining_initial_sum = total_sum - removed_sum

        leaves = (n + 1) // 2

        if leaves == 0 or torn >= leaves:
            expected = 0.0
        elif torn <= 0:
            expected = float(remaining_initial_sum)
        else:
            expected = remaining_initial_sum * (leaves - torn) / leaves

        answers.append(f"{expected:.4f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()
