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
            a = data[idx]
            idx += 1

            # 0 can never satisfy the condition with any number
            if a == 0:
                continue

            bit = a.bit_length()
            ans += freq.get(bit, 0)
            freq[bit] = freq.get(bit, 0) + 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()