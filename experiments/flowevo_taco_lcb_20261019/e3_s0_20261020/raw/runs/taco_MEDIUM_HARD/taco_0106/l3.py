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

        s = data[idx].decode()
        idx += 1
        a = data[idx].decode()
        idx += 1

        # If A is already a subsequence of the fixed characters of S,
        # replacing '?' cannot remove A.
        j = 0
        for ch in s:
            if ch != '?' and j < m and ch == a[j]:
                j += 1
                if j == m:
                    break

        if j == m:
            answers.append("-1")
            continue

        # Construct S' by making every '?' not match the currently needed
        # character of A. This keeps the matched prefix unchanged.
        res = []
        j = 0

        for ch in s:
            if ch == '?':
                # j < m is guaranteed because fixed characters do not contain A.
                if a[j] == 'a':
                    res.append('e')
                else:
                    res.append('a')
            else:
                res.append(ch)
                if j < m and ch == a[j]:
                    j += 1

        answers.append(''.join(res))

    sys.stdout.write('\n'.join(answers))


if __name__ == "__main__":
    solve()