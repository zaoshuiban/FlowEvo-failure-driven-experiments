import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        m = int(data[idx + 1])
        idx += 2

        s = data[idx]
        idx += 1
        a = data[idx]
        idx += 1

        # Check whether A is already a subsequence of the fixed characters of S.
        j = 0
        for ch in s:
            if ch != ord('?') and j < m and ch == a[j]:
                j += 1
                if j == m:
                    break

        if j == m:
            answers.append(b"-1")
            continue

        # Construct a valid S'.
        res = bytearray()
        j = 0

        for ch in s:
            if ch == ord('?'):
                # Pick a character different from the next required character of A.
                if j < m and a[j] == ord('a'):
                    res.append(ord('b'))
                else:
                    res.append(ord('a'))
            else:
                res.append(ch)
                if j < m and ch == a[j]:
                    j += 1

        answers.append(bytes(res))

    sys.stdout.buffer.write(b"\n".join(answers))


if __name__ == "__main__":
    solve()