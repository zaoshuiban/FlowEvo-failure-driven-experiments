import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    freq = {}
    idx = 1

    for _ in range(n):
        a = int(data[idx])
        b = int(data[idx + 1])
        c = int(data[idx + 2])
        idx += 3

        key = tuple(sorted((a, b, c)))
        freq[key] = freq.get(key, 0) + 1

    unique_count = 0
    for count in freq.values():
        if count == 1:
            unique_count += 1

    sys.stdout.write(str(unique_count))

if __name__ == "__main__":
    main()