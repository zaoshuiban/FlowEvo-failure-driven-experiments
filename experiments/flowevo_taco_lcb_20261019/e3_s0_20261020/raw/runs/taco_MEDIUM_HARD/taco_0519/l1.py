import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        a = data[idx:idx + n]
        idx += n

        best_i = 0
        best_diff = a[k] - a[0]

        for i in range(1, n - k):
            diff = a[i + k] - a[i]
            if diff < best_diff:
                best_diff = diff
                best_i = i

        left = a[best_i]
        right = a[best_i + k]
        answers.append(str((left + right) // 2))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()