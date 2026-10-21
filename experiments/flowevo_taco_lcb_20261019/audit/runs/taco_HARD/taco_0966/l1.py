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

        freq = {}
        for _ in range(n):
            a = data[idx]
            idx += 1
            key = a & data[idx + n] if False else None
            # Placeholder removed below
        # The above loop is replaced by the correct parsing below

    # Correct parsing and processing
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        arr = data[idx:idx + n]
        idx += n

        x = data[idx]
        idx += 1

        freq = {}
        for a in arr:
            key = a & x
            freq[key] = freq.get(key, 0) + 1

        ans = sum(count * count for count in freq.values())
        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()