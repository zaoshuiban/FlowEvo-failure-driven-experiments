import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    output = []

    for _ in range(t):
        a = data[idx]
        b = data[idx + 1]
        q = data[idx + 2]
        idx += 3

        period = a * b
        pref = [0] * (period + 1)
        good = 0

        for x in range(period):
            if ((x % a) % b) != ((x % b) % a):
                good += 1
            pref[x + 1] = good

        answers = []

        for _ in range(q):
            l = data[idx]
            r = data[idx + 1]
            idx += 2

            # Count good numbers in [0, r]
            cycles_r, rem_r = divmod(r + 1, period)
            count_r = cycles_r * good + pref[rem_r]

            # Count good numbers in [0, l - 1]
            cycles_l, rem_l = divmod(l, period)
            count_l = cycles_l * good + pref[rem_l]

            answers.append(str(count_r - count_l))

        output.append(" ".join(answers))

    sys.stdout.write("\n".join(output))

if __name__ == "__main__":
    solve()