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
        for _ in range(n):
            x = data[idx]
            idx += 1
            freq[x] = freq.get(x, 0) + 1

        distinct = len(freq)
        repeated = sum(1 for count in freq.values() if count >= 2)

        answers.append(str((distinct + repeated + 1) // 2))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()