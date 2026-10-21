import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        arr = data[idx:idx + n]
        idx += n

        x = data[idx]
        idx += 1

        freq = {}
        for value in arr:
            key = value & x
            freq[key] = freq.get(key, 0) + 1

        ans = sum(count * count for count in freq.values())
        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()