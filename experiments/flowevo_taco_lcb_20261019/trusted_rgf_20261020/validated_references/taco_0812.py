import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    answers = []

    for _ in range(T):
        N = next(it)
        M = next(it)

        first = [-1] * (N + 1)
        last = [-1] * (N + 1)

        for i in range(M):
            x = next(it)
            if first[x] == -1:
                first[x] = i
            last[x] = i

        end_first = [-1] * M

        for value in range(1, N + 1):
            pos = last[value]
            if first[value] > end_first[pos]:
                end_first[pos] = first[value]

        max_keep = 0
        max_first = -1

        for r in range(M):
            if end_first[r] > max_first:
                max_first = end_first[r]

            keep_length = r - max_first
            if keep_length > max_keep:
                max_keep = keep_length

        answers.append(str(M - max_keep))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()