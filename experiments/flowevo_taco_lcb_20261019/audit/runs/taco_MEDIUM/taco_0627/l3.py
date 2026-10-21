import sys

def solve():
    data = sys.stdin.buffer.read()
    length = len(data)
    idx = 0

    def next_int():
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    t = next_int()
    answers = []

    for _ in range(t):
        s = next_int()

        q = [0] * s
        for i in range(s):
            q[i] = next_int()

        total_time = 0

        for season in range(s):
            episodes = next_int()
            season_sum = 0

            for _ in range(episodes):
                season_sum += next_int()

            total_time += season_sum - (episodes - 1) * q[season]

        answers.append(str(total_time))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()