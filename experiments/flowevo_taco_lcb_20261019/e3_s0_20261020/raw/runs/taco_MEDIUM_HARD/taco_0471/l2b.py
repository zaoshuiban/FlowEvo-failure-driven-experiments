import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        count = [0] * 32
        ans = 0

        for _ in range(n):
            a = data[idx]
            idx += 1

            bit = a.bit_length()
            ans += count[bit]
            count[bit] += 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()