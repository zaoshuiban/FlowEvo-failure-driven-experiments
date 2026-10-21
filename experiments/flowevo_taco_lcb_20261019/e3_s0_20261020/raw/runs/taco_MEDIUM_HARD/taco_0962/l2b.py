import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        s = data[i]
        n = len(s)

        mask = 0
        for ch in s:
            mask ^= 1 << (ch - ord('a'))

        odd_count = mask.bit_count()

        if n >= 3 * odd_count:
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()