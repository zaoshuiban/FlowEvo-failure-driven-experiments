import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    output = []

    for _ in range(t):
        n = next(it)
        a = [next(it) for _ in range(n)]

        depth = [0] * n

        def build(left: int, right: int, d: int) -> None:
            if left >= right:
                return

            max_idx = left
            for i in range(left + 1, right):
                if a[i] > a[max_idx]:
                    max_idx = i

            depth[max_idx] = d

            build(left, max_idx, d + 1)
            build(max_idx + 1, right, d + 1)

        build(0, n, 0)
        output.append(" ".join(map(str, depth)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()