import sys


def int_generator():
    data = sys.stdin.buffer.read()
    num = 0
    inside = False

    for ch in data:
        if 48 <= ch <= 57:
            num = num * 10 + (ch - 48)
            inside = True
        else:
            if inside:
                yield num
                num = 0
                inside = False

    if inside:
        yield num


def solve():
    it = int_generator()

    try:
        n = next(it)
    except StopIteration:
        return

    m = next(it)

    adj = [[] for _ in range(n)]

    for _ in range(m):
        a = next(it) - 1
        b = next(it) - 1
        c = next(it)

        # We need: chosen[a] xor chosen[b] = 1 xor c
        need = 1 - c
        adj[a].append((b, need))
        adj[b].append((a, need))

    value = [-1] * n
    answer = []

    for start in range(n):
        if value[start] != -1:
            continue

        value[start] = 0
        stack = [start]
        component = []

        while stack:
            u = stack.pop()
            component.append(u)

            for v, need in adj[u]:
                expected = value[u] ^ need

                if value[v] == -1:
                    value[v] = expected
                    stack.append(v)
                elif value[v] != expected:
                    sys.stdout.write("Impossible\n")
                    return

        ones = []
        zeros = []

        for u in component:
            if value[u] == 1:
                ones.append(u + 1)
            else:
                zeros.append(u + 1)

        # Flipping all values inside a connected component keeps every XOR unchanged.
        if len(ones) <= len(zeros):
            answer.extend(ones)
        else:
            answer.extend(zeros)

    sys.stdout.write(str(len(answer)) + "\n")
    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    solve()