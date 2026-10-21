import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    answers = []

    for _ in range(T):
        N = next(it)
        tasks = [next(it) for _ in range(N)]

        total = sum(tasks)
        prefix = 0
        answer = total  # Assign all tasks to the second processor

        for time in tasks:
            prefix += time
            suffix = total - prefix
            answer = min(answer, max(prefix, suffix))

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()