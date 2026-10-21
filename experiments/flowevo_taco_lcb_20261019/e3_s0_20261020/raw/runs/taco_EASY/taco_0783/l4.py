import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        s = data[idx]
        idx += 1

        freq = [0] * 4
        left = 0
        distinct = 0
        best = len(s) + 1

        for right, ch in enumerate(s):
            value = ch - ord('0')

            if freq[value] == 0:
                distinct += 1
            freq[value] += 1

            while distinct == 3:
                best = min(best, right - left + 1)

                left_value = s[left] - ord('0')
                freq[left_value] -= 1
                if freq[left_value] == 0:
                    distinct -= 1
                left += 1

        answers.append(str(best if best <= len(s) else 0))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()