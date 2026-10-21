import sys
import heapq


def solve():
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    t = int(next(it))
    answers = []

    heappush = heapq.heappush
    heappop = heapq.heappop
    heapify = heapq.heapify

    for _ in range(t):
        n = int(next(it))
        m = int(next(it))

        v1 = [int(next(it)) for _ in range(n)]
        d1 = next(it)

        v2 = [int(next(it)) for _ in range(m)]
        d2 = next(it)

        total1 = sum(v1)
        total2 = sum(v2)

        attack1 = []
        defense1 = []

        attack2 = []
        defense2 = []

        for val, mode in zip(v1, d1):
            if mode == ord('A'):
                attack1.append(val)
            else:
                defense1.append(-val)

        for val, mode in zip(v2, d2):
            if mode == ord('A'):
                attack2.append(val)
            else:
                defense2.append(-val)

        attack1.sort()
        attack2.sort()

        heapify(defense1)
        heapify(defense2)

        delta = total1 - total2
        deltas = [delta]

        i = 0
        j = 0
        turn = 0  # 0 -> Chef, 1 -> Chefina

        len_attack1 = len(attack1)
        len_attack2 = len(attack2)

        while True:
            if turn == 0:
                if i >= len_attack1 or not defense2:
                    break

                used_attack = attack1[i]
                i += 1

                heappush(defense1, -used_attack)
                killed_defense = -heappop(defense2)

                delta += killed_defense
                deltas.append(delta)
                turn = 1

            else:
                if j >= len_attack2 or not defense1:
                    break

                used_attack = attack2[j]
                j += 1

                heappush(defense2, -used_attack)
                killed_defense = -heappop(defense1)

                delta -= killed_defense
                deltas.append(delta)
                turn = 0

        value = deltas[-1]

        for k in range(len(deltas) - 2, -1, -1):
            if k & 1:
                if deltas[k] < value:
                    value = deltas[k]
            else:
                if deltas[k] > value:
                    value = deltas[k]

        answers.append(str(value))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()