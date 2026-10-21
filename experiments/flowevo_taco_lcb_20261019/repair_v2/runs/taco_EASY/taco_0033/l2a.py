import sys

def solve():
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        q = int(next(it))
        s = next(it)

        freq = [0] * 26
        for ch in s:
            freq[ch - 97] += 1

        for _ in range(q):
            c = int(next(it))
            pending = 0

            for f in freq:
                if f > c:
                    pending += f - c

            answers.append(str(pending))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()