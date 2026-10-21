import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        xor_sum = 0

        for i in range(1, n + 1):
            a = int(next(it))

            if i & 1:          # Odd-indexed pile
                xor_sum ^= (a & 1)
            else:              # Even-indexed pile
                xor_sum ^= (a >> 1)

        answers.append("CHEF" if xor_sum else "CHEFINA")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()