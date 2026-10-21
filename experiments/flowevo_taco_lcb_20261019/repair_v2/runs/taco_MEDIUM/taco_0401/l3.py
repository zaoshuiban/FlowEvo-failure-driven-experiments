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
        idx += 1

        zeros = 0
        positives = []

        for _ in range(n):
            x = data[idx]
            idx += 1
            if x == 0:
                zeros += 1
            else:
                positives.append(x)

        positives.sort()

        capacity = n - 1
        used = 0
        ans = zeros

        for x in positives:
            if used + x <= capacity:
                used += x
                ans += 1
            else:
                break

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()