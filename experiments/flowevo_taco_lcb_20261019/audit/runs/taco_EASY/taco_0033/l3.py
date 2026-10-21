import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    idx = 0
    t = int(data[idx])
    idx += 1

    answers = []

    for _ in range(t):
        n = int(data[idx])
        q = int(data[idx + 1])
        idx += 2

        s = data[idx]
        idx += 1

        freq = [0] * 26
        for ch in s:
            freq[ch - 97] += 1

        frequencies = [f for f in freq if f > 0]

        for _ in range(q):
            c = int(data[idx])
            idx += 1

            pending = 0
            for f in frequencies:
                if f > c:
                    pending += f - c

            answers.append(str(pending))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()