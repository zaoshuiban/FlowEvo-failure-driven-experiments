import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        s = data[idx]
        idx += 1

        freq = [0] * 26
        for ch in s:
            freq[ch - ord('a')] += 1

        odd_count = 0
        pair_count = 0

        for count in freq:
            odd_count += count & 1
            pair_count += count // 2

        if pair_count >= odd_count:
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()