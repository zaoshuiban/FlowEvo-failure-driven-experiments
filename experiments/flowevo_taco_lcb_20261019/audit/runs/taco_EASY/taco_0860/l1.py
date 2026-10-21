import sys
from collections import Counter

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    freq = Counter()
    idx = 1

    for _ in range(n):
        sides = tuple(sorted((data[idx], data[idx + 1], data[idx + 2])))
        freq[sides] += 1
        idx += 3

    unique_count = sum(1 for count in freq.values() if count == 1)
    print(unique_count)

if __name__ == "__main__":
    main()