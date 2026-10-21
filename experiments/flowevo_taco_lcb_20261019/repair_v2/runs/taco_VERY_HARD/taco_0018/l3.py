import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, r = data[0], data[1]
    size = 1 << n

    values = data[2:2 + size]
    total = sum(values)

    idx = 2 + size
    out = []

    SCALE = 10 ** 12

    def add_answer(total_sum: int) -> None:
        integer_part, remainder = divmod(total_sum, size)
        fractional_part = remainder * SCALE // size
        out.append(f"{integer_part}.{fractional_part:012d}")

    add_answer(total)

    for _ in range(r):
        z = data[idx]
        g = data[idx + 1]
        idx += 2

        total += g - values[z]
        values[z] = g

        add_answer(total)

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()