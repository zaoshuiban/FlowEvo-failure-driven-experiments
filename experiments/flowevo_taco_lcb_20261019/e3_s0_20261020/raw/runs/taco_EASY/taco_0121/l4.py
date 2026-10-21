import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        k = int(next(it))

        vote_count = {}
        self_voters = set()

        for person in range(1, n + 1):
            voted_for = int(next(it))
            vote_count[voted_for] = vote_count.get(voted_for, 0) + 1

            if voted_for == person:
                self_voters.add(person)

        government_size = 0

        for person, votes in vote_count.items():
            if votes >= k and person not in self_voters:
                government_size += 1

        answers.append(str(government_size))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()