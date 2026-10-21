import sys

def solve():
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    T = int(next(it))
    answers = []

    for _ in range(T):
        N = int(next(it))
        Q = int(next(it))
        S = next(it)

        freq = [0] * 26
        for ch in S:
            freq[ch - ord('a')] += 1

        for _ in range(Q):
            C = int(next(it))
            pending = 0

            for count in freq:
                if count > C:
                    pending += count - C

            answers.append(str(pending))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()