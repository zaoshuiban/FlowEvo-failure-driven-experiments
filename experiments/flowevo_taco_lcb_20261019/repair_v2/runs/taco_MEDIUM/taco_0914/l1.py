import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        freq = {}

        for _ in range(n):
            x = next(it)
            freq[x] = freq.get(x, 0) + 1

        twice_or_more = 0
        once = 0

        for count in freq.values():
            if count == 1:
                once += 1
            else:
                twice_or_more += 1

        answers.append(str(twice_or_more + (once + 1) // 2))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()