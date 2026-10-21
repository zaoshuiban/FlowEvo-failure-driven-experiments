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
            page = data[idx]
            idx += 1
            if 1 <= page <= n:
                unprinted.add(page)

        torn = data[idx]
        idx += 1

        total_sum = n * (n + 1) // 2
        printed_sum = total_sum - sum(unprinted)

        leaves = (n + 1) // 2

        if leaves == 0:
            expected = 0.0
        else:
            torn = min(torn, leaves)
            expected = printed_sum * (leaves - torn) / leaves

        answers.append(f"{expected:.4f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()
