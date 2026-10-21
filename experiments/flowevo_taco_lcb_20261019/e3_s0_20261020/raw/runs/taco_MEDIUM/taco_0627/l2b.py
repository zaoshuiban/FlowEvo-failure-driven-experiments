import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        s = data[idx]
        idx += 1

        q = data[idx:idx + s]
        idx += s

        total_time = 0

        for season in range(s):
            episodes = data[idx]
            idx += 1

            episode_sum = 0
            for _ in range(episodes):
                episode_sum += data[idx]
                idx += 1

            total_time += episode_sum - (episodes - 1) * q[season]

        answers.append(str(total_time))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()