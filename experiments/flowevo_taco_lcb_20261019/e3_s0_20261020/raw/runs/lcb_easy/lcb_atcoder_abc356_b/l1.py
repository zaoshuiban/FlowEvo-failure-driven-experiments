import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    N, M = data[0], data[1]
    A = data[2:2 + M]

    idx = 2 + M
    totals = [0] * M

    for _ in range(N):
        for j in range(M):
            totals[j] += data[idx]
            idx += 1

    print("Yes" if all(totals[j] >= A[j] for j in range(M)) else "No")


if __name__ == "__main__":
    main()