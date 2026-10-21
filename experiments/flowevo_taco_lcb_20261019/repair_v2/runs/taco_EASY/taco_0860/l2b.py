import sys
from collections import Counter

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    freq = Counter()

    index = 1
    for _ in range(n):
        a = int(data[index])
        b = int(data[index + 1])
        c = int(data[index + 2])
        index += 3

        sides = tuple(sorted((a, b, c)))
        freq[sides] += 1

    unique_count = sum(1 for count in freq.values() if count == 1)
    print(unique_count)

if __name__ == "__main__":
    main()