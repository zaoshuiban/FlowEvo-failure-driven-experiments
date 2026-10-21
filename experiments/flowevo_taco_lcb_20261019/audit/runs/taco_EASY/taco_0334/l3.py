import sys
from collections import Counter

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

        arr = data[idx:idx + n]
        idx += n

        total_pairs = n * (n - 1) // 2
        freq = Counter(arr)
        values = sorted(freq.keys(), reverse=True)

        largest = values[0]

        if freq[largest] >= 2:
            favorable = freq[largest] * (freq[largest] - 1) // 2
        else:
            second_largest = values[1]
            favorable = freq[largest] * freq[second_largest]

        probability = favorable / total_pairs
        answers.append(f"{probability:.10f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()