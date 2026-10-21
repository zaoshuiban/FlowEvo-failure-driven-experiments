import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    pos = 1
    answers = []
    A_CHAR = 65  # ord('A')

    for _ in range(t):
        n = int(data[pos])
        m = int(data[pos + 1])
        pos += 2

        start1 = pos
        d1 = data[start1 + n]

        attack1 = []
        defense1 = []
        sum1 = 0

        for i in range(n):
            value = int(data[start1 + i])
            sum1 += value
            if d1[i] == A_CHAR:
                attack1.append(value)
            else:
                defense1.append(value)

        pos = start1 + n + 1

        start2 = pos
        d2 = data[start2 + m]

        attack2 = []
        defense2 = []
        sum2 = 0

        for i in range(m):
            value = int(data[start2 + i])
            sum2 += value
            if d2[i] == A_CHAR:
                attack2.append(value)
            else:
                defense2.append(value)

        pos = start2 + m + 1

        attack1.sort()
        attack2.sort()
        defense1.sort(reverse=True)
        defense2.sort(reverse=True)

        len_a1 = len(attack1)
        len_a2 = len(attack2)
        len_d1 = len(defense1)
        len_d2 = len(defense2)

        idx_a1 = 0
        idx_a2 = 0
        idx_d1 = 0
        idx_d2 = 0

        # Newly exposed defense monsters from used attack monsters.
        # For each player these values are appended in non-decreasing order.
        exposed1 = []
        exposed2 = []

        sequence = []
        turn = 0  # 0 = Chef, 1 = Chefina

        while True:
            if turn == 0:
                if idx_a1 >= len_a1 or (idx_d2 >= len_d2 and not exposed2):
                    break

                value_initial = defense2[idx_d2] if idx_d2 < len_d2 else -1
                value_exposed = exposed2[-1] if exposed2 else -1

                if value_initial >= value_exposed:
                    target = value_initial
                    idx_d2 += 1
                else:
                    target = value_exposed
                    exposed2.pop()

                sequence.append(target)

                exposed1.append(attack1[idx_a1])
                idx_a1 += 1
                turn = 1

            else:
                if idx_a2 >= len_a2 or (idx_d1 >= len_d1 and not exposed1):
                    break

                value_initial = defense1[idx_d1] if idx_d1 < len_d1 else -1
                value_exposed = exposed1[-1] if exposed1 else -1

                if value_initial >= value_exposed:
                    target = value_initial
                    idx_d1 += 1
                else:
                    target = value_exposed
                    exposed1.pop()

                sequence.append(-target)

                exposed2.append(attack2[idx_a2])
                idx_a2 += 1
                turn = 0

        future = 0

        for i in range(len(sequence) - 1, -1, -1):
            candidate = sequence[i] + future

            if i & 1:
                # Chefina's turn: she minimizes Chef's score difference.
                if candidate < 0:
                    future = candidate
                else:
                    future = 0
            else:
                # Chef's turn: he maximizes Chef's score difference.
                if candidate > 0:
                    future = candidate
                else:
                    future = 0

        answers.append(str(sum1 - sum2 + future))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()