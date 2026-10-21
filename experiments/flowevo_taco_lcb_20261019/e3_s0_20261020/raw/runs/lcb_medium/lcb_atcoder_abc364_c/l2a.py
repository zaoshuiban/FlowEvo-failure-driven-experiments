import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    N = next(it)
    X = next(it)
    Y = next(it)

    A = [next(it) for _ in range(N)]
    B = [next(it) for _ in range(N)]

    dishes = list(zip(A, B))
    ans = N

    for idx in (0, 1):
        ordered = sorted(dishes, key=lambda p: p[idx], reverse=True)
        sum_a = 0
        sum_b = 0

        for i, (a, b) in enumerate(ordered, 1):
            sum_a += a
            sum_b += b

            if sum_a > X or sum_b > Y:
                ans = min(ans, i)
                break

    print(ans)


if __name__ == "__main__":
    solve()