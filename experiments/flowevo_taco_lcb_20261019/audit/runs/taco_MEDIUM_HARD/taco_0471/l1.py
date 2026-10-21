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

        count = [0] * 32

        for _ in range(n):
            x = data[idx]
            idx += 1
            if x > 0:
                count[x.bit_length()] += 1

        ans = 0
        for c in count:
            ans += c * (c - 1) // 2

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()