import sys

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

        freq = {}
        for score in scores:
            freq[score] = freq.get(score, 0) + 1

        count_less_equal = 0
        answer = 0

        for score in sorted(freq):
            count_less_equal += freq[score]

            if 2 * count_less_equal > n:
                answer += freq[score]

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()