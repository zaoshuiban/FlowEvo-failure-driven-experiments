import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        freq = [0] * 32

        for _ in range(n):
            a = data[idx]
            idx += 1
            freq[a.bit_length()] += 1

        ans = 0
        for count in freq:
            ans += count * (count - 1) // 2

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()