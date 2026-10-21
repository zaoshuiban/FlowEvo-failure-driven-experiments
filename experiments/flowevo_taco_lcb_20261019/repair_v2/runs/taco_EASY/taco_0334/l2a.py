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

        a = data[idx:idx + n]
        idx += n

        max_sum = -1
        count_max = 0

        for i in range(n):
            for j in range(i + 1, n):
                current_sum = a[i] + a[j]
                if current_sum > max_sum:
                    max_sum = current_sum
                    count_max = 1
                elif current_sum == max_sum:
                    count_max += 1

        total_pairs = n * (n - 1) // 2
        probability = count_max / total_pairs
        answers.append(f"{probability:.8f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()