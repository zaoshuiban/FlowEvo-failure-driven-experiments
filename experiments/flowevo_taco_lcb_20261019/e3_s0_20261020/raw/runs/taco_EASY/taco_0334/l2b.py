import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        a = data[idx:idx + n]
        idx += n

        max_sum = -1
        count = 0

        for i in range(n):
            for j in range(i + 1, n):
                s = a[i] + a[j]
                if s > max_sum:
                    max_sum = s
                    count = 1
                elif s == max_sum:
                    count += 1

        total_pairs = n * (n - 1) // 2
        probability = count / total_pairs
        answers.append(f"{probability:.10f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()