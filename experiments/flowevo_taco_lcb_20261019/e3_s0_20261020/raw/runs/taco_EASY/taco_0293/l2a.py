import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        has_odd = False
        even_count = 0
        min_twos = 10**9

        for _ in range(n):
            x = data[idx]
            idx += 1

            if x & 1:
                has_odd = True
            else:
                even_count += 1
                v2 = (x & -x).bit_length() - 1
                if v2 < min_twos:
                    min_twos = v2

        if has_odd:
            answers.append(str(even_count))
        else:
            answers.append(str(min_twos + n - 1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()