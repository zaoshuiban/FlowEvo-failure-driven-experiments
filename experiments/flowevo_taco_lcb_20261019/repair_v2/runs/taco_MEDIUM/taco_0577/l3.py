import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        l, r, m = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        max_diff = r - l

        for a in range(l, r + 1):
            n = m // a

            # Try n = floor(m / a), only if n is positive.
            if n >= 1:
                d = m - n * a  # b - c
                if d <= max_diff:
                    b = l + d
                    c = l
                    ans.append(f"{a} {b} {c}")
                    break

            # Try n = floor(m / a) + 1.
            n += 1
            d = m - n * a  # b - c, usually negative here
            if abs(d) <= max_diff:
                if d >= 0:
                    b = l + d
                    c = l
                else:
                    b = l
                    c = l - d
                ans.append(f"{a} {b} {c}")
                break

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()