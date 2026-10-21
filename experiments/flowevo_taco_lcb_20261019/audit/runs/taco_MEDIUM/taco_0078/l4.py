import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        scores = data[idx:idx + n]
        idx += n

        scores.sort()
        ans = 0
        i = 0

        while i < n:
            j = i + 1
            while j < n and scores[j] == scores[i]:
                j += 1

            less_equal = j
            greater = n - less_equal

            if less_equal > greater:
                ans += j - i

            i = j

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()