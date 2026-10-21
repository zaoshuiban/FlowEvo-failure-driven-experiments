import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:1 + n]

    suffix = [0] * (n + 1)
    seen = bytearray(n + 1)

    distinct = 0
    for i in range(n - 1, -1, -1):
        v = a[i]
        if not seen[v]:
            seen[v] = 1
            distinct += 1
        suffix[i] = distinct

    seen = bytearray(n + 1)
    distinct = 0
    answer = 0

    for i in range(n - 1):
        v = a[i]
        if not seen[v]:
            seen[v] = 1
            distinct += 1

        answer = max(answer, distinct + suffix[i + 1])

    print(answer)

if __name__ == "__main__":
    main()