import sys


def solve() -> None:
    data = sys.stdin.buffer.read()
    if not data:
        return

    idx = 0
    length = len(data)

    def next_int() -> int:
        nonlocal idx
        while idx < length and data[idx] <= 32:
            idx += 1
        num = 0
        while idx < length and data[idx] > 32:
            num = num * 10 + (data[idx] - 48)
            idx += 1
        return num

    n = next_int()
    k = next_int()

    parent = list(range(n))
    size = [1] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for _ in range(k):
        u = next_int() - 1
        v = next_int() - 1
        ru = find(u)
        rv = find(v)

        if ru != rv:
            if size[ru] < size[rv]:
                ru, rv = rv, ru
            parent[rv] = ru
            size[ru] += size[rv]

    m = next_int()
    bad = [False] * n

    for _ in range(m):
        u = next_int() - 1
        v = next_int() - 1
        ru = find(u)
        rv = find(v)

        if ru == rv:
            bad[ru] = True

    answer = 0

    for i in range(n):
        if parent[i] == i and not bad[i]:
            answer = max(answer, size[i])

    print(answer)


if __name__ == "__main__":
    solve()