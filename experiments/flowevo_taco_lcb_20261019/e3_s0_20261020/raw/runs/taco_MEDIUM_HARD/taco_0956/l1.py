import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        idx += 1

        a = data[idx]
        idx += 1

        b = data[idx]
        idx += 1

        parent = list(range(20))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        ans = 0
        possible = True

        for ca, cb in zip(a, b):
            x = ca - ord('a')
            y = cb - ord('a')

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