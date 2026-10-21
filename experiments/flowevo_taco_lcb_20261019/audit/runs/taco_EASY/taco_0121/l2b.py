import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)

        votes = [next(it) for _ in range(n)]
        count = [0] * (n + 1)

        for person in votes:
            count[person] += 1

        government_size = 0

        for person in range(1, n + 1):
            voted_for_self = votes[person - 1] == person

            if not voted_for_self and count[person] >= k:
                government_size += 1

        answers.append(str(government_size))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()