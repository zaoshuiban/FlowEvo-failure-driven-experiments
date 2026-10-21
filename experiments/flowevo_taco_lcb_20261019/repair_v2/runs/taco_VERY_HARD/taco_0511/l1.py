import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    out = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        a = data[idx:idx + n]
        idx += n

        s = data[idx:idx + k]
        idx += k

        max_val = -1
        pos = -1
        for i, val in enumerate(a):
            if val > max_val:
                max_val = val
                pos = i

        s.sort()

        # Number of discs above the maximum-valued disc.
        r_init = pos
        below = n - pos - 1

        win = bytearray(r_init + 1)
        s_idx = -1

        for r in range(r_init + 1):
            total = r + 1 + below

            while s_idx + 1 < k and s[s_idx + 1] <= total:
                s_idx += 1

            # Current player can take the maximum disc immediately.
            if s[s_idx] > r:
                win[r] = 1
            else:
                # Otherwise, make a move that does not take the maximum disc.
                for x in s:
                    if x > r:
                        break
                    if win[r - x] == 0:
                        win[r] = 1
                        break

        out.append("Chef" if win[r_init] else "Garry")

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()