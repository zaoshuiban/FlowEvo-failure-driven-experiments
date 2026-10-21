import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        nxt = [0] * (n + 1)
        off_diagonal = 0

        for _ in range(m):
            x = next(it)
            y = next(it)

            if x != y:
                nxt[x] = y
                off_diagonal += 1

        state = bytearray(n + 1)
        cycles = 0

        for start in range(1, n + 1):
            if nxt[start] != 0 and state[start] == 0:
                path = []
                u = start

                while u != 0 and state[u] == 0:
                    state[u] = 1
                    path.append(u)
                    u = nxt[u]

                if u != 0 and state[u] == 1:
                    cycles += 1

                for v in path:
                    state[v] = 2

        answers.append(str(off_diagonal + cycles))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()