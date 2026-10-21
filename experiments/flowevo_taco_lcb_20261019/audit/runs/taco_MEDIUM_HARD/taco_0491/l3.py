import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        b = data[idx:idx + n]
        idx += n

        ans = 0

        for bit in range(29, -1, -1):
            mask = ans | (1 << bit)

            count = {}
            for x in a:
                value = x & mask
                count[value] = count.get(value, 0) + 1

            possible = True
            for x in b:
                value = (x & mask) ^ mask
                c = count.get(value, 0)

                if c == 0:
                    possible = False
                    break

                if c == 1:
                    del count[value]
                else:
                    count[value] = c - 1

            if possible:
                ans = mask

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()