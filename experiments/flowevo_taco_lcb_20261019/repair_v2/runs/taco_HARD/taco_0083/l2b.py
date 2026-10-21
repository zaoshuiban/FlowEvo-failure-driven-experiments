import sys


def int_generator():
    data = sys.stdin.buffer.read()
    num = 0
    inside = False
    for b in data:
        if 48 <= b <= 57:
            num = num * 10 + (b - 48)
            inside = True
        else:
            if inside:
                yield num
                num = 0
                inside = False
    if inside:
        yield num


def solve():
    it = iter(int_generator())

    try:
        n = next(it)
        m = next(it)
    except StopIteration:
        return

    adj = [[] for _ in range(n)]

    for _ in range(m):
        a = next(it) - 1
        b = next(it) - 1
        c = next(it)

        need = 1 - c
        adj[a].append((b << 1) | need)
        adj[b].append((a << 1) | need)

    value = [-1] * n
    answer = []

    for start in range(n):
        if value[start] != -1:
            continue

        value[start] = 0
        stack = [start]

        while stack:
            u = stack.pop()

            if value[u] == 1:
                answer.append(u + 1)

            for edge in adj[u]:
                v = edge >> 1
                need = edge & 1
                expected = value[u] ^ need

                if value[v] == -1:
                    value[v] = expected
                    stack.append(v)
                elif value[v] != expected:
                    print("Impossible")
                    return

    output = [
        str(len(answer)),
        "\n",
        " ".join(map(str, answer)),
        "\n"
    ]
    sys.stdout.write("".join(output))


if __name__ == "__main__":
    solve()