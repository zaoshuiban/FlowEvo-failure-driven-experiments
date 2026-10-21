import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        votes = data[idx:idx + n]
        idx += n

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