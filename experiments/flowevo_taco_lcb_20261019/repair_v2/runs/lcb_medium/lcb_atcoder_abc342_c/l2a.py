import sys


def main():
    data = sys.stdin.buffer.read().split()

    n = int(data[0])
    s = data[1]
    q = int(data[2])

    operations = []
    idx = 3

    for _ in range(q):
        c = data[idx][0] - ord('a')
        d = data[idx + 1][0] - ord('a')
        operations.append((c, d))
        idx += 2

    mapping = list(range(26))

    for c, d in reversed(operations):
        mapping[c] = mapping[d]

    result = []
    for ch in s:
        result.append(chr(mapping[ch - ord('a')] + ord('a')))

    print(''.join(result))


if __name__ == "__main__":
    main()