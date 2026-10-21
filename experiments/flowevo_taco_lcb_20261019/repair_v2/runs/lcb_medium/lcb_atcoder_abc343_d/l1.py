import sys
from collections import defaultdict

def main():
    input = sys.stdin.buffer.readline

    N, T = map(int, input().split())

    score = [0] * (N + 1)
    count = defaultdict(int)
    count[0] = N

    distinct = 1
    answers = []

    for _ in range(T):
        a, b = map(int, input().split())

        old_score = score[a]
        count[old_score] -= 1
        if count[old_score] == 0:
            distinct -= 1

        new_score = old_score + b
        score[a] = new_score

        if count[new_score] == 0:
            distinct += 1
        count[new_score] += 1

        answers.append(str(distinct))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()