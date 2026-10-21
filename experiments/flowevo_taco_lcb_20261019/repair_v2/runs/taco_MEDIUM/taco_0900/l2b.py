import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)

        prefix_odd = [0] * (n + 1)

        for i in range(1, n + 1):
            value = next(it)
            prefix_odd[i] = prefix_odd[i - 1] + (value & 1)

        q = next(it)

        for _ in range(q):
            l = next(it)
            r = next(it)

            odd_count = prefix_odd[r] - prefix_odd[l - 1]
            length = r - l + 1

            if odd_count == length:
                answers.append("ODD")
            else:
                answers.append("EVEN")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()