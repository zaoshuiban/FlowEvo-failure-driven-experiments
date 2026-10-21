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

        unprinted_sum = 0
        seen = set()

        for _ in range(f):
            page = data[idx]
            idx += 1
            if page not in seen:
                seen.add(page)
                if 1 <= page <= n:
                    unprinted_sum += page

        torn = data[idx]
        idx += 1

        total_sum = n * (n + 1) // 2
        printed_sum = total_sum - unprinted_sum

        leaves = (n + 1) // 2

        if leaves == 0 or torn >= leaves:
            expected = 0.0
        else:
            expected = printed_sum * (leaves - torn) / leaves

        answers.append(f"{expected:.4f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()
