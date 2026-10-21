import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        idx += 2

        q = [0] * m
        first = [0] * (n + 1)
        last = [0] * (n + 1)

        for i in range(m):
            v = data[idx]
            idx += 1
            q[i] = v

            if first[v] == 0:
                first[v] = i + 1
            last[v] = i + 1

        max_first = 0
        max_keep = 0

        for r in range(1, m + 1):
            v = q[r - 1]

            if last[v] == r:
                if first[v] > max_first:
                    max_first = first[v]

            keep_len = r - max_first
            if keep_len > max_keep:
                max_keep = keep_len

        answers.append(str(m - max_keep))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()