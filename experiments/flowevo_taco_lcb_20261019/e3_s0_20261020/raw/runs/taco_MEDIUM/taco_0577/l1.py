import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        l = int(data[idx])
        r = int(data[idx + 1])
        m = int(data[idx + 2])
        idx += 3

        d_range = r - l
        lower = m - d_range
        upper = m + d_range

        for a in range(l, r + 1):
            if lower <= 0:
                n = 1
            else:
                n = (lower + a - 1) // a

            prod = n * a

            if prod <= upper:
                diff = m - prod  # b - c

                if diff >= 0:
                    b = l + diff
                    c = l
                else:
                    b = l
                    c = l - diff

                answers.append(f"{a} {b} {c}")
                break

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()