import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for case in range(1, t + 1):
        s = data[case]
        n = len(s)

        count = [0, 0, 0]
        distinct = 0
        left = 0
        ans = n + 1

        for right, ch in enumerate(s):
            idx = ch - ord('1')
            if count[idx] == 0:
                distinct += 1
            count[idx] += 1

            while distinct == 3:
                ans = min(ans, right - left + 1)

                left_idx = s[left] - ord('1')
                count[left_idx] -= 1

                if count[left_idx] == 0:
                    distinct -= 1

                left += 1

        answers.append(str(ans if ans <= n else 0))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()