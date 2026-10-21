import sys

def solve():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(data)
    answers = []

    for _ in range(t):
        n = next(data)
        k = next(data)

        votes_for = [0] * (n + 1)
        vote_count = [0] * (n + 1)

        for person in range(1, n + 1):
            voted_for = next(data)
            votes_for[person] = voted_for
            vote_count[voted_for] += 1

        government_size = 0

        for person in range(1, n + 1):
            if vote_count[person] >= k and votes_for[person] != person:
                government_size += 1

        answers.append(str(government_size))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()