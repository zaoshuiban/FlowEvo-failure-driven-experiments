import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)

        even_count = 0
        min_v2 = 10**18

        for _ in range(n):
            x = next(it)

            if x % 2 == 0:
                even_count += 1

                lowbit = x & -x
                v2 = lowbit.bit_length() - 1
                if v2 < min_v2:
                    min_v2 = v2

        if even_count == 0:
            answers.append("0")
        elif even_count < n:
            answers.append(str(even_count))
        else:
            answers.append(str(min_v2 + n - 1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()