import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    freq = {}
    idx = 1

    for _ in range(n):
        a, b, c = data[idx], data[idx + 1], data[idx + 2]
        idx += 3

        sides = tuple(sorted((a, b, c)))
        freq[sides] = freq.get(sides, 0) + 1

    answer = sum(1 for count in freq.values() if count == 1)
    print(answer)

if __name__ == "__main__":
    main()