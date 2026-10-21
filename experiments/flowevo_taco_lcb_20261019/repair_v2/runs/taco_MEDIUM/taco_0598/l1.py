import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        weights = [next(it) for _ in range(n)]
        jumps = [next(it) for _ in range(n)]

        order = sorted(range(n), key=lambda i: weights[i])

        prev_position = -10**18
        hits = 0

        for idx in order:
            start_position = idx + 1
            step = jumps[idx]

            if start_position > prev_position:
                k = 0
            else:
                k = (prev_position - start_position) // step + 1

            final_position = start_position + k * step
            hits += k
            prev_position = final_position

        answers.append(str(hits))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()