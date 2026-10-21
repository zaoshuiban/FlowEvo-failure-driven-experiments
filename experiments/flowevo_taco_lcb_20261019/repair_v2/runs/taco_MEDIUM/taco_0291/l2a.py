import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
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

        total_sum = n * (n + 1) // 2
        visible_sum = total_sum - sum(missing)

        leaves = (n + 1) // 2

        if leaves == 0:
            expected = 0.0
        else:
            expected = visible_sum * (leaves - torn) / leaves

        answers.append(f"{expected:.4f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()