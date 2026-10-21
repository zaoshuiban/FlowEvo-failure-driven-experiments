import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        k = next(it)
        L = next(it)

        speeds = [next(it) for _ in range(n)]

        friend_speed = speeds[-1]

        if n == 1:
            answers.append("Yes")
            continue

        max_other_speed = max(speeds[:-1])

        if k > 0:
            best_speed = friend_speed + (L - 1) * k
            if best_speed > max_other_speed:
                answers.append("Yes")
            else:
                answers.append("No")
        else:
            if friend_speed > max_other_speed:
                answers.append("Yes")
            else:
                answers.append("No")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()