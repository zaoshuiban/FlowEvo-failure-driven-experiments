import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for case in range(t):
        s = data[case + 1]
        n = len(s)

        freq = [0] * 26
        for ch in s:
            freq[ch - 97] += 1

        odd_count = sum(count & 1 for count in freq)

        if n >= 3 * odd_count:
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()