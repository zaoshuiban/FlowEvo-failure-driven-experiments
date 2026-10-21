import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        freq = {}
        ans = 0

        for _ in range(n):
            x = data[idx]
            idx += 1

            # Zero can never satisfy the condition with any number.
            if x == 0:
                continue

            highest_bit = x.bit_length()
            count = freq.get(highest_bit, 0)
            ans += count
            freq[highest_bit] = count + 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()