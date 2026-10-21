import sys
from math import gcd

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        prev = data[idx]
        idx += 1

        in_vals = []
        in_gcd = []
        out_gcd = []

        window_len = 0
        best = 0

        for _ in range(1, n):
            cur = data[idx]
            idx += 1

            diff = prev - cur
            if diff < 0:
                diff = -diff
            prev = cur

            in_vals.append(diff)
            if in_gcd:
                in_gcd.append(gcd(in_gcd[-1], diff))
            else:
                in_gcd.append(diff)

            window_len += 1

            while window_len > 0:
                gout = out_gcd[-1] if out_gcd else 0
                gin = in_gcd[-1] if in_gcd else 0
                current_gcd = gcd(gout, gin)

                if current_gcd != 1:
                    break

                if not out_gcd:
                    while in_vals:
                        val = in_vals.pop()
                        in_gcd.pop()

                        prev_gcd = out_gcd[-1] if out_gcd else 0
                        out_gcd.append(gcd(prev_gcd, val))

                out_gcd.pop()
                window_len -= 1

            if window_len > best:
                best = window_len

        answers.append(str(best + 1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()