import sys

def solve():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(data)
    answers = []

    for _ in range(t):
        s = next(data)

        q = [next(data) for _ in range(s)]

        total_time = 0

        for season in range(s):
            episodes = next(data)

            season_sum = 0
            for _ in range(episodes):
                season_sum += next(data)

            total_time += season_sum - (episodes - 1) * q[season]

        answers.append(str(total_time))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()