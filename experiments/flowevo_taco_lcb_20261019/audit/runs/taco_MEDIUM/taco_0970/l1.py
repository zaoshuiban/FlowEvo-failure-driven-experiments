import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    frequencies = data[idx:idx + n]
    idx += n

    k = data[idx]
    idx += 1

    key_sizes = data[idx:idx + k]

    if sum(key_sizes) < n:
        print(-1)
        return

    frequencies.sort(reverse=True)

    costs = []
    for size in key_sizes:
        for position in range(1, size + 1):
            costs.append(position)

    costs.sort()

    answer = sum(frequencies[i] * costs[i] for i in range(n))
    print(answer)

if __name__ == "__main__":
    main()