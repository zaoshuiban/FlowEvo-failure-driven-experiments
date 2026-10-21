import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    it = iter(data)

    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        m = int(next(it))

        size = n + 1
        stride_x = size * size

        bit = [0] * (size * size * size)
        values = {}

        def prefix(x: int, y: int, z: int) -> int:
            total = 0

            i = x
            while i > 0:
                base_x = i * stride_x

                j = y
                while j > 0:
                    base_xy = base_x + j * size

                    k = z
                    while k > 0:
                        total += bit[base_xy + k]
                        k -= k & -k

                    j -= j & -j

                i -= i & -i

            return total

        for _ in range(m):
            operation = next(it)

            if operation[0] == ord('U'):  # UPDATE
                x = int(next(it))
                y = int(next(it))
                z = int(next(it))
                w = int(next(it))

                key = x * stride_x + y * size + z
                previous = values.get(key, 0)
                delta = w - previous
                values[key] = w

                if delta != 0:
                    i = x
                    while i <= n:
                        base_x = i * stride_x

                        j = y
                        while j <= n:
                            base_xy = base_x + j * size

                            k = z
                            while k <= n:
                                bit[base_xy + k] += delta
                                k += k & -k

                            j += j & -j

                        i += i & -i

            else:  # QUERY
                x1 = int(next(it))
                y1 = int(next(it))
                z1 = int(next(it))
                x2 = int(next(it))
                y2 = int(next(it))
                z2 = int(next(it))

                result = prefix(x2, y2, z2)
                result -= prefix(x1 - 1, y2, z2)
                result -= prefix(x2, y1 - 1, z2)
                result -= prefix(x2, y2, z1 - 1)

                result += prefix(x1 - 1, y1 - 1, z2)
                result += prefix(x1 - 1, y2, z1 - 1)
                result += prefix(x2, y1 - 1, z1 - 1)

                result -= prefix(x1 - 1, y1 - 1, z1 - 1)

                answers.append(str(result))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()