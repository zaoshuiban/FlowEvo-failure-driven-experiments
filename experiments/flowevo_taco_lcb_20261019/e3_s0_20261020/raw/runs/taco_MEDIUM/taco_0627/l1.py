import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        s = next(it)
        intro = [next(it) for _ in range(s)]

        total_time = 0

        for i in range(s):
            e = next(it)

            episode_sum = 0
            for _ in range(e):
                episode_sum += next(it)

            total_time += episode_sum - intro[i] * (e - 1)

        answers.append(str(total_time))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()