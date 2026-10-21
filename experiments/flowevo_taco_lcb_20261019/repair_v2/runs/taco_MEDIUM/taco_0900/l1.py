import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)

        prefix_even = [0] * (n + 1)

        for i in range(1, n + 1):
            value = next(it)
            prefix_even[i] = prefix_even[i - 1] + (1 if value % 2 == 0 else 0)

        q = next(it)

        for _ in range(q):
            l = next(it)
            r = next(it)

            even_count = prefix_even[r] - prefix_even[l - 1]

            if even_count == 0:
                answers.append("ODD")
            else:
                answers.append("EVEN")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()