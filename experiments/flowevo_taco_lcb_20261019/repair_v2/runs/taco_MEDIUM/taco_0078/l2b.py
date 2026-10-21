import sys
from collections import Counter

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        scores = data[idx:idx + n]
        idx += n

        freq = Counter(scores)
        count_less_equal = 0
        boast_count = 0

        for score in sorted(freq):
            count_less_equal += freq[score]
            count_greater = n - count_less_equal

            if count_less_equal > count_greater:
                boast_count += freq[score]

        answers.append(str(boast_count))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()