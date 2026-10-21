import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        L = data[idx + 2]
        idx += 3

        speeds = data[idx:idx + n]
        idx += n

        if n == 1:
            answers.append("Yes")
            continue

        friend_speed = speeds[-1]
        max_other_speed = max(speeds[:-1])

        # If k > 0, using the maximum allowed drug units is optimal.
        # Allowed units must be < L, so maximum is L - 1.
        # If k <= 0, using any drug cannot improve the speed, so use 0.
        if k > 0:
            friend_speed += (L - 1) * k

        if friend_speed > max_other_speed:
            answers.append("Yes")
        else:
            answers.append("No")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()