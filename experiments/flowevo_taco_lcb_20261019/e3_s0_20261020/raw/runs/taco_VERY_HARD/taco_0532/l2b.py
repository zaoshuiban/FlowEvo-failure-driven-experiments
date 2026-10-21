import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        d = data[idx + 1]
        idx += 2

        p = data[idx:idx + n]
        idx += n

        possible = True
        for i, value in enumerate(p, 1):
            if (value - i) % d != 0:
                possible = False
                break

        if not possible:
            answers.append("-1")
            continue

        ans = 0

        for first in range(1, d + 1):
            m = (n - first) // d + 1

            if m <= 1:
                continue

            if m <= 32:
                seq = []
                for pos in range(first, n + 1, d):
                    seq.append((p[pos - 1] - first) // d)

                inv = 0
                for i in range(m - 1):
                    x = seq[i]
                    for j in range(i + 1, m):
                        if x > seq[j]:
                            inv += 1

                ans += inv

            else:
                bit = [0] * (m + 1)
                processed = 0

                for pos in range(first, n + 1, d):
                    rank = (p[pos - 1] - first) // d
                    bit_idx = rank + 1

                    prefix_sum = 0
                    j = bit_idx
                    while j > 0:
                        prefix_sum += bit[j]
                        j -= j & -j

                    ans += processed - prefix_sum

                    j = bit_idx
                    while j <= m:
                        bit[j] += 1
                        j += j & -j

                    processed += 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()