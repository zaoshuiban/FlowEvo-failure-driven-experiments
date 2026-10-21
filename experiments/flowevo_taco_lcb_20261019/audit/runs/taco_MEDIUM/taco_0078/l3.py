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

        scores = data[idx:idx + n]
        idx += n

        freq = {}
        for score in scores:
            freq[score] = freq.get(score, 0) + 1

        less_equal = 0
        boast_count = 0

        for score in sorted(freq):
            less_equal += freq[score]
            greater = n - less_equal

            if less_equal > greater:
                boast_count += freq[score]

        answers.append(str(boast_count))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()