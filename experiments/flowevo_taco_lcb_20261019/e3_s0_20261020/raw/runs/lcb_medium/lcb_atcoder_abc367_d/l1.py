import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, M = data[0], data[1]
    A = data[2:2 + N]

    size = 2 * N - 1
    prefix = [0] * size

    cur = 0
    for i in range(1, size):
        cur = (cur + A[(i - 1) % N]) % M
        prefix[i] = cur

    freq = [0] * M

    for i in range(1, N):
        freq[prefix[i]] += 1

    ans = 0

    for p in range(N):
        ans += freq[prefix[p]]

        if p < N - 1:
            freq[prefix[p + 1]] -= 1
            freq[prefix[p + N]] += 1

    print(ans)

if __name__ == "__main__":
    main()