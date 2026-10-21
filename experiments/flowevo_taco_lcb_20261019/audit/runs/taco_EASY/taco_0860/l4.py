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

        x, y, z = sorted((a, b, c))
        key = (x, y, z)
        freq[key] = freq.get(key, 0) + 1

    unique_count = sum(1 for count in freq.values() if count == 1)
    sys.stdout.write(str(unique_count) + "\n")

if __name__ == "__main__":
    main()