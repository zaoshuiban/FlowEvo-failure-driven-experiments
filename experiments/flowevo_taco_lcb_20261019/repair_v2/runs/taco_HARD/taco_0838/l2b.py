import sys
from itertools import permutations

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])

    color_id = [0] * 256
    color_id[ord('r')] = 0
    color_id[ord('g')] = 1
    color_id[ord('b')] = 2

    answers = []

    for case in range(1, t + 1):
        s = data[case]

        count = [0, 0, 0]
        cross = [[0, 0, 0] for _ in range(3)]
        # cross[a][b] = number of pairs where color a appears before color b

        for ch in s:
            c = color_id[ch]

            cross[0][c] += count[0]
            cross[1][c] += count[1]
            cross[2][c] += count[2]

            count[c] += 1

        present = [c for c in range(3) if count[c] > 0]

        if len(present) <= 1:
            answers.append("0")
            continue

        best = 10**30

        for order in permutations(present):
            cost = 0
            m = len(order)

            for i in range(m):
                for j in range(i + 1, m):
                    earlier = order[i]
                    later = order[j]
                    # In the target, earlier must be before later.
                    # Every later before earlier in the source must be swapped.
                    cost += cross[later][earlier]

            if cost < best:
                best = cost

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()