import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    t = data[idx]
    idx += 1
    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        shift = n + m + 5
        prev = [0] * m

        for i in range(n):
            curr = [0] * m

            for j in range(m):
                val = data[idx]
                idx += 1

                if i == 0:
                    if j == 0:
                        curr[j] = 1 << (shift + val)
                    else:
                        if val == 1:
                            curr[j] = curr[j - 1] << 1
                        else:
                            curr[j] = curr[j - 1] >> 1
                else:
                    if j == 0:
                        bits = prev[j]
                    else:
                        bits = prev[j] | curr[j - 1]

                    if val == 1:
                        curr[j] = bits << 1
                    else:
                        curr[j] = bits >> 1

            prev = curr

        zero_bit = 1 << shift
        answers.append("YES" if (prev[m - 1] & zero_bit) else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()