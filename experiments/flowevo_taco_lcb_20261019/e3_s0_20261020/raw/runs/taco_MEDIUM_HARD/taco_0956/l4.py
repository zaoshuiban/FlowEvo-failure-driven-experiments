import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    pos = 1
    answers = []

    for _ in range(t):
        n = int(data[pos])
        pos += 1
        a = data[pos]
        pos += 1
        b = data[pos]
        pos += 1

        need = [[False] * 20 for _ in range(20)]
        possible = True

        for ca, cb in zip(a, b):
            x = ca - 97
            y = cb - 97

            if x > y:
                possible = False
                break

            if x < y:
                need[x][y] = True

        if not possible:
            answers.append("-1")
            continue

        ans = 0

        for x in range(20):
            y = -1

            for z in range(x + 1, 20):
                if need[x][z]:
                    y = z
                    break

            if y != -1:
                ans += 1

                for z in range(y + 1, 20):
                    if need[x][z]:
                        need[y][z] = True

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()