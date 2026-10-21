import sys

def solve():
    data = sys.stdin.read().split()
    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        idx += 1
        A = data[idx]
        idx += 1
        B = data[idx]
        idx += 1

        parent = list(range(20))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        possible = True
        ans = 0

        for a, b in zip(A, B):
            x = ord(a) - ord('a')
            y = ord(b) - ord('a')

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

    print("\n".join(answers))


if __name__ == "__main__":
    solve()