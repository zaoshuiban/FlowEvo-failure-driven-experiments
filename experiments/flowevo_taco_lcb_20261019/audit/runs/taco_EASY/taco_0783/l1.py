import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        s = data[idx]
        idx += 1

        count = [0, 0, 0]
        distinct = 0
        left = 0
        answer = len(s) + 1

        for right, ch in enumerate(s):
            c = ch - ord('1')
            if count[c] == 0:
                distinct += 1
            count[c] += 1

            while distinct == 3:
                answer = min(answer, right - left + 1)

                left_c = s[left] - ord('1')
                count[left_c] -= 1
                if count[left_c] == 0:
                    distinct -= 1
                left += 1

        answers.append(str(answer if answer <= len(s) else 0))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()