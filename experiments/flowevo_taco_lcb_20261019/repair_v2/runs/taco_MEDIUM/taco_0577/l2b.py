import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        l, r, m = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        max_diff = r - l

        for a in range(l, r + 1):
            q, rem = divmod(m, a)

            # Try n = q, if q is positive
            if q >= 1 and rem <= max_diff:
                d = rem  # b - c
                if d >= 0:
                    b, c = l + d, l
                else:
                    b, c = l, l - d
                answers.append(f"{a} {b} {c}")
                break

            # Try n = q + 1
            d = rem - a  # m - (q + 1) * a = b - c
            if abs(d) <= max_diff:
                if d >= 0:
                    b, c = l + d, l
                else:
                    b, c = l, l - d
                answers.append(f"{a} {b} {c}")
                break

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()