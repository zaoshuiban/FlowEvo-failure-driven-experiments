import sys
from array import array
from bisect import bisect_left

MOD = 1_000_000_007


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    max_r = 0
    idx = 1

    for _ in range(t):
        r = data[idx + 1]
        if r > max_r:
            max_r = r
        idx += 2

    # g[i] = G_i
    # prefA[v] = sum_{i=1}^v G_i, the last position where value v occurs
    # prefP[v] = sum_{i=1}^v i^2 * G_i
    g = array('I', [0, 1])
    prefA = array('Q', [0, 1])
    prefP = array('I', [0, 1])

    while prefA[-1] < max_r:
        cur = len(g) - 1
        nxt = cur + 1

        gg = g[g[cur]]
        val = 1 + g[nxt - gg]

        g.append(val)
        prefA.append(prefA[-1] + val)

        add = (nxt * nxt % MOD) * val % MOD
        prefP.append((prefP[-1] + add) % MOD)

    def prefix_sum_squares(n):
        if n <= 0:
            return 0

        v = bisect_left(prefA, n)
        remaining = n - prefA[v - 1]

        add = (remaining % MOD) * (v * v % MOD) % MOD
        return (prefP[v - 1] + add) % MOD

    answers = []
    idx = 1

    for _ in range(t):
        left = data[idx]
        right = data[idx + 1]
        idx += 2

        ans = (prefix_sum_squares(right) - prefix_sum_squares(left - 1)) % MOD
        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()