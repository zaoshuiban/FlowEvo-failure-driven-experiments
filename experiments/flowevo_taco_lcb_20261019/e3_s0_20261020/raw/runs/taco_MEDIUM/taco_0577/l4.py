import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        l, r, m = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        max_diff = r - l

        for a in range(l, r + 1):
            # n = floor(m / a)
            n = m // a
            d = m - n * a  # b - c

            if n >= 1 and -max_diff <= d <= max_diff:
                if d >= 0:
                    b = l + d
                    c = l
                else:
                    b = l
                    c = l - d
                answers.append(f"{a} {b} {c}")
                break

            # n = floor(m / a) + 1
            n += 1
            d = m - n * a

            if n >= 1 and -max_diff <= d <= max_diff:
                if d >= 0:
                    b = l + d
                    c = l
                else:
                    b = l
                    c = l - d
                answers.append(f"{a} {b} {c}")
                break

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()