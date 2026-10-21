import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    idx = 1
    answers = []

    QUESTION = ord('?')
    LETTER_A = ord('a')
    LETTER_B = ord('b')

    for _ in range(t):
        n = int(data[idx])
        m = int(data[idx + 1])
        idx += 2

        s = bytearray(data[idx])
        idx += 1

        a = data[idx]
        idx += 1

        j = 0  # length of the matched prefix of A
        possible = True

        for i, ch in enumerate(s):
            if ch == QUESTION:
                # Choose a character different from the next needed character of A.
                # This keeps j unchanged.
                if a[j] == LETTER_A:
                    s[i] = LETTER_B
                else:
                    s[i] = LETTER_A
            else:
                if j < m and ch == a[j]:
                    j += 1
                    if j == m:
                        possible = False
                        break

        if possible:
            answers.append(s.decode())
        else:
            answers.append("-1")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()