import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, T = data[0], data[1]

    scores = [0] * N
    freq = {0: N}
    distinct = 1

    answers = []
    idx = 2

    for _ in range(T):
        player = data[idx] - 1
        increase = data[idx + 1]
        idx += 2

        old_score = scores[player]
        new_score = old_score + increase

        freq[old_score] -= 1
        if freq[old_score] == 0:
            del freq[old_score]
            distinct -= 1

        if new_score in freq:
            freq[new_score] += 1
        else:
            freq[new_score] = 1
            distinct += 1

        scores[player] = new_score
        answers.append(str(distinct))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()