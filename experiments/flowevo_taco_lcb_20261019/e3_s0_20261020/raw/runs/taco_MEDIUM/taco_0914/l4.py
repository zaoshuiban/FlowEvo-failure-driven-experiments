import sys

def solve() -> None:
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
        end = idx + n

        while idx < end:
            x = data[idx]
            idx += 1
            freq[x] = freq.get(x, 0) + 1

        single = 0
        repeated = 0

        for count in freq.values():
            if count == 1:
                single += 1
            else:
                repeated += 1

        answers.append(str(repeated + (single + 1) // 2))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()