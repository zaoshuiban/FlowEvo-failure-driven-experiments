import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    QUESTION = ord('?')
    A_CHAR = ord('a')
    E_CHAR = ord('e')

    for _ in range(t):
        n = int(data[idx])
        m = int(data[idx + 1])
        idx += 2

        s = data[idx]
        idx += 1
        a = data[idx]
        idx += 1

        # If A is already a subsequence using only fixed characters of S,
        # then it is impossible to avoid A.
        j = 0
        for ch in s:
            if ch != QUESTION and j < m and ch == a[j]:
                j += 1
                if j == m:
                    break

        if j == m:
            answers.append(b"-1")
            continue

        # Build S' greedily. At every '?', put a character different from
        # the currently needed character of A, so it cannot extend the
        # matched prefix of A.
        res = bytearray()
        j = 0

        for ch in s:
            if ch == QUESTION:
                if j < m and a[j] == A_CHAR:
                    res.append(E_CHAR)
                else:
                    res.append(A_CHAR)
            else:
                res.append(ch)
                if j < m and ch == a[j]:
                    j += 1

        answers.append(bytes(res))

    sys.stdout.buffer.write(b"\n".join(answers))


if __name__ == "__main__":
    solve()