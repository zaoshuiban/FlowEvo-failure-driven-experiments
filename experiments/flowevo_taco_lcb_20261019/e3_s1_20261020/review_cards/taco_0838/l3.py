import sys
from itertools import permutations


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])

    color_id = [0] * 256
    color_id[ord('r')] = 0
    color_id[ord('g')] = 1
    color_id[ord('b')] = 2

    orders = list(permutations((0, 1, 2)))
    answers = []

    idx = 1
    for _ in range(t):
        s = data[idx]
        idx += 1

        arr = [color_id[ch] for ch in s]
        best = 10**30

        for order in orders:
            rank = [0, 0, 0]
            for pos, color in enumerate(order):
                rank[color] = pos

            seen = [0, 0, 0]
            cost = 0

            for color in arr:
                r = rank[color]

                # Previously seen colors that should appear after this color
                # form inversions with the current container.
                for j in range(r + 1, 3):
                    cost += seen[order[j]]

                seen[color] += 1

            if cost < best:
                best = cost

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()