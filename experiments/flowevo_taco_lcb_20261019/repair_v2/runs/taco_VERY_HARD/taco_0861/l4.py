import sys


def solve() -> None:
    tokens = sys.stdin.buffer.read().split()
    if not tokens:
        return

    it = iter(map(int, tokens))
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        stack_values = []
        stack_indices = []
        last = {}
        total = 0

        for i in range(n):
            v = next(it)

            while stack_values and stack_values[-1] >= v:
                stack_values.pop()
                stack_indices.pop()

            left_smaller = stack_indices[-1] if stack_indices else -1
            previous_same = last.get(v, -1)

            if previous_same <= left_smaller:
                total += 1

            last[v] = i
            stack_values.append(v)
            stack_indices.append(i)

        answers.append(str(total - 1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()