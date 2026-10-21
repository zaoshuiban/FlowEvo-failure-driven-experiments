import sys
from heapq import heapify, heappop, heappush


class FastScanner:
    def __init__(self):
        self.data = sys.stdin.buffer.read()
        self.idx = 0
        self.n = len(self.data)

    def next_int(self):
        data = self.data
        n = self.n
        i = self.idx

        while i < n and data[i] <= 32:
            i += 1

        num = 0
        while i < n and data[i] > 32:
            num = num * 10 + (data[i] - 48)
            i += 1

        self.idx = i
        return num

    def next_token(self):
        data = self.data
        n = self.n
        i = self.idx

        while i < n and data[i] <= 32:
            i += 1

        start = i
        while i < n and data[i] > 32:
            i += 1

        self.idx = i
        return data[start:i]


def solve():
    fs = FastScanner()
    t = fs.next_int()
    answers = []

    for _ in range(t):
        n = fs.next_int()
        m = fs.next_int()

        values1 = [0] * n
        total1 = 0
        for i in range(n):
            x = fs.next_int()
            values1[i] = x
            total1 += x

        d1 = fs.next_token()

        attack1 = []
        defense1 = []

        for i, ch in enumerate(d1):
            if ch == 65:  # 'A'
                attack1.append(values1[i])
            else:
                defense1.append(-values1[i])

        values2 = [0] * m
        total2 = 0
        for i in range(m):
            x = fs.next_int()
            values2[i] = x
            total2 += x

        d2 = fs.next_token()

        attack2 = []
        defense2 = []

        for i, ch in enumerate(d2):
            if ch == 65:  # 'A'
                attack2.append(values2[i])
            else:
                defense2.append(-values2[i])

        attack1.sort()
        attack2.sort()

        heapify(defense1)
        heapify(defense2)

        current = total1 - total2
        values_path = [current]

        ptr1 = 0
        ptr2 = 0
        len_attack1 = len(attack1)
        len_attack2 = len(attack2)

        turn = 0  # 0 -> Chef, 1 -> Chefina

        while True:
            if turn == 0:
                if ptr1 >= len_attack1 or not defense2:
                    break

                attacker = attack1[ptr1]
                ptr1 += 1

                killed = -heappop(defense2)
                current += killed
                heappush(defense1, -attacker)

                values_path.append(current)
                turn = 1

            else:
                if ptr2 >= len_attack2 or not defense1:
                    break

                attacker = attack2[ptr2]
                ptr2 += 1

                killed = -heappop(defense1)
                current -= killed
                heappush(defense2, -attacker)

                values_path.append(current)
                turn = 0

        result = values_path[-1]

        for i in range(len(values_path) - 2, -1, -1):
            value = values_path[i]

            if i % 2 == 0:  # Chef's turn
                if value > result:
                    result = value
            else:  # Chefina's turn
                if value < result:
                    result = value

        answers.append(str(result))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()