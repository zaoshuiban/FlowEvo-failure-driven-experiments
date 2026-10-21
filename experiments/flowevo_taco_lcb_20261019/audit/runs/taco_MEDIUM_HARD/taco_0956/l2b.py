import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        a = next(it)
        b = next(it)

        parent = list(range(20))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        possible = True
        ans = 0

        for i in range(n):
            x = a[i] - ord('a')
            y = b[i] - ord('a')

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