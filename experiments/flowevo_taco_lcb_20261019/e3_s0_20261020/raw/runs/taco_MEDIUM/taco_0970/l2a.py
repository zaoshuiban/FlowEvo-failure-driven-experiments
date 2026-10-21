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

    positions = []
    for size in key_sizes:
        positions.extend(range(1, size + 1))

    positions.sort()

    answer = sum(freq * pos for freq, pos in zip(frequencies, positions[:n]))
    print(answer)

if __name__ == "__main__":
    main()