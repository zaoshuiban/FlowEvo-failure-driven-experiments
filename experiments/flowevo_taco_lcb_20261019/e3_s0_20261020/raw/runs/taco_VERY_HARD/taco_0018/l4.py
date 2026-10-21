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

    DIGITS = 15
    SCALE = 10 ** DIGITS

    def append_answer(value_sum: int) -> None:
        integer_part, remainder = divmod(value_sum, size)
        fractional_part = remainder * SCALE // size
        out.append(f"{integer_part}.{fractional_part:0{DIGITS}d}")

    append_answer(total)

    for _ in range(r):
        z = data[idx]
        g = data[idx + 1]
        idx += 2

        total += g - values[z]
        values[z] = g

        append_answer(total)

    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    solve()