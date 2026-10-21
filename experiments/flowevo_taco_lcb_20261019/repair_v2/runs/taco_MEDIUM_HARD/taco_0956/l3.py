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

        parent = list(range(20))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        possible = True
        ans = 0

        for ca, cb in zip(a, b):
            x = ca - 97
            y = cb - 97

            if x > y:
                possible = False
                break

            if x < y:
                rx = find(x)
                ry = find(y)

                if rx != ry:
                    parent[rx] = ry
                    ans += 1

        answers.append(str(ans) if possible else "-1")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()