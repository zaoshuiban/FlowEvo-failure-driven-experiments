import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    answers = []

    for _ in range(T):
        S = next(it)

        intro = [next(it) for _ in range(S)]

        total_time = 0

        for season in range(S):
            episodes = next(it)

            season_sum = 0
            for _ in range(episodes):
                season_sum += next(it)

            total_time += season_sum - (episodes - 1) * intro[season]

        answers.append(str(total_time))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()