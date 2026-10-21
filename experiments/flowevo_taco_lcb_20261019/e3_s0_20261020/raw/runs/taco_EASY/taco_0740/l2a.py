import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    output = []

    sys.setrecursionlimit(10000)

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        depths = [0] * n

        def build(left, right, depth):
            if left > right:
                return

            max_pos = left
            for i in range(left + 1, right + 1):
                if a[i] > a[max_pos]:
                    max_pos = i

            depths[max_pos] = depth

            build(left, max_pos - 1, depth + 1)
            build(max_pos + 1, right, depth + 1)

        build(0, n - 1, 0)

        output.append(" ".join(map(str, depths)))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()