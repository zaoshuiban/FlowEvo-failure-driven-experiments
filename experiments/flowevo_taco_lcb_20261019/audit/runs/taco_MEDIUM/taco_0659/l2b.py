import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    idx = 0
    t = int(data[idx])
    idx += 1

    answers = []

    for _ in range(t):
        n = int(data[idx])
        l = int(data[idx + 1])
        idx += 2

        a = list(map(int, data[idx:idx + n]))
        idx += n
        b = a[::-1]

        lo = 0.0
        hi = float(l)

        for _ in range(100):
            mid = (lo + hi) / 2.0

            # Position of the first car at time mid
            rem = mid
            speed = 1.0
            prev = 0.0
            pos_left = 0.0

            for x in a:
                time_to_flag = (x - prev) / speed
                if rem >= time_to_flag:
                    rem -= time_to_flag
                    prev = float(x)
                    speed += 1.0
                else:
                    pos_left = prev + speed * rem
                    break
            else:
                pos_left = prev + speed * rem

            # Position of the second car at time mid
            rem = mid
            speed = 1.0
            prev = float(l)
            pos_right = float(l)

            for x in b:
                time_to_flag = (prev - x) / speed
                if rem >= time_to_flag:
                    rem -= time_to_flag
                    prev = float(x)
                    speed += 1.0
                else:
                    pos_right = prev - speed * rem
                    break
            else:
                pos_right = prev - speed * rem

            if pos_left >= pos_right:
                hi = mid
            else:
                lo = mid

        answers.append(f"{hi:.15f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()