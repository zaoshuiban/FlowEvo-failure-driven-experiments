import sys

def covered(t, flags):
    pos = 0.0
    elapsed = 0.0
    speed = 1

    for d in flags:
        need = (d - pos) / speed
        if elapsed + need <= t:
            elapsed += need
            pos = d
            speed += 1
        else:
            break

    return pos + (t - elapsed) * speed


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        l = data[idx + 1]
        idx += 2

        a = data[idx:idx + n]
        idx += n

        reversed_flags = [l - a[i] for i in range(n - 1, -1, -1)]

        low = 0.0
        high = float(l)

        for _ in range(80):
            mid = (low + high) / 2.0

            first = covered(mid, a)
            second = covered(mid, reversed_flags)

            if first + second >= l:
                high = mid
            else:
                low = mid

        answers.append(f"{high:.15f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()