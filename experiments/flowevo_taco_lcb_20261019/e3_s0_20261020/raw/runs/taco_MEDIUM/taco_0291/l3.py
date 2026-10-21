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

        total_all = n * (n + 1) // 2
        unprinted_sum = sum(p for p in unprinted if 1 <= p <= n)
        total_printed = total_all - unprinted_sum

        leaves = (n + 1) // 2  # ceil(n / 2)

        if leaves == 0:
            expected = 0.0
        else:
            effective_torn = min(max(torn, 0), leaves)
            expected = total_printed * (leaves - effective_torn) / leaves

        answers.append(f"{expected:.4f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()