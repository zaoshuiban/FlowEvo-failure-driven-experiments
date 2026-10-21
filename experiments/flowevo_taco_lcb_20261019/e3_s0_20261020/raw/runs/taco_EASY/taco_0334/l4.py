import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        arr = data[idx:idx + n]
        idx += n

        max_sum = -10**18
        favorable = 0

        for i in range(n):
            for j in range(i + 1, n):
                current_sum = arr[i] + arr[j]

                if current_sum > max_sum:
                    max_sum = current_sum
                    favorable = 1
                elif current_sum == max_sum:
                    favorable += 1

        total_pairs = n * (n - 1) // 2
        probability = favorable / total_pairs
        answers.append(f"{probability:.12f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    main()