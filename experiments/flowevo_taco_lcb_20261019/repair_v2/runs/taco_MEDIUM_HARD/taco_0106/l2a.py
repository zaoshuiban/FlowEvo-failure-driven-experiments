import sys


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    QUESTION = ord('?')
    A_CHAR = ord('a')
    B_CHAR = ord('b')

    for _ in range(t):
        n = int(data[idx])
        m = int(data[idx + 1])
        idx += 2

        s = data[idx]
        idx += 1
        a = data[idx]
        idx += 1

        res = bytearray()
        matched = 0

        for ch in s:
            if ch == QUESTION:
                if matched < m:
                    # Choose any character != a[matched]
                    if a[matched] == A_CHAR:
                        res.append(B_CHAR)
                    else:
                        res.append(A_CHAR)
                else:
                    res.append(A_CHAR)
            else:
                res.append(ch)
                if matched < m and ch == a[matched]:
                    matched += 1

        if matched == m:
            answers.append("-1")
        else:
            answers.append(res.decode())

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()