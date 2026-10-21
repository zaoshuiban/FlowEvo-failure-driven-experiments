import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
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

        single = 0
        multiple = 0

        for count in freq.values():
            if count == 1:
                single += 1
            else:
                multiple += 1

        ans = multiple + (single + 1) // 2
        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()