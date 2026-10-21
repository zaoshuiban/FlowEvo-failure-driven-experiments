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
        idx += 1

        d = data[idx:idx + n]
        idx += n

        d.sort()

        max_d = d[-1]

        # Sum of all optimal negative edges:
        # for every ordered pair (u, v) with d[u] > d[v],
        # add weight d[v] - d[u].
        negative_sum = 0
        for i, value in enumerate(d):
            negative_sum += value * (n - 1 - 2 * i)

        answers.append(str(max_d + negative_sum))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()