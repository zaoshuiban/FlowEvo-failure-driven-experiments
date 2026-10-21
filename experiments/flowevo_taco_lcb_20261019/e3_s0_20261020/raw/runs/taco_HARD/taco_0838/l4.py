import sys
from itertools import permutations


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1

    orders = list(permutations((0, 1, 2)))
    answers = []

    R = ord('r')
    G = ord('g')

    for _ in range(t):
        # Some versions may include N before the string; skip it if present.
        if idx < len(data) and data[idx].isdigit():
            idx += 1

        s = data[idx]
        idx += 1

        best = 10**30

        for order in orders:
            rank = [0, 0, 0]
            for pos, color in enumerate(order):
                rank[color] = pos

            seen = [0, 0, 0]
            cost = 0

            for ch in s:
                if ch == R:
                    color = 0
                elif ch == G:
                    color = 1
                else:
                    color = 2

                r = rank[color]

                if r == 0:
                    cost += seen[order[1]] + seen[order[2]]
                elif r == 1:
                    cost += seen[order[2]]

                seen[color] += 1

            if cost < best:
                best = cost

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()