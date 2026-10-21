import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        xor_sum = 0

        for i in range(1, n + 1):
            a = data[idx]
            idx += 1

            if i & 1:
                grundy = a & 1
            else:
                grundy = a >> 1

            xor_sum ^= grundy

        answers.append("CHEF" if xor_sum else "CHEFINA")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()