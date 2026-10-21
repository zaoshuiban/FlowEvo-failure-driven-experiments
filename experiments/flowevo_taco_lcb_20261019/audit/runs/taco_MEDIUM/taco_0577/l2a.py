import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        l = data[idx]
        r = data[idx + 1]
        m = data[idx + 2]
        idx += 3

        D = r - l

        for a in range(l, r + 1):
            n = (m + D) // a

            if n >= 1:
                prod = n * a

                if prod >= m - D:
                    d = m - prod

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