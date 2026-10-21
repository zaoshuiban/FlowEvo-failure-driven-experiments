import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    p = data[1:1 + n]

    inversions = 0
    for i in range(n):
        for j in range(i + 1, n):
            if p[i] > p[j]:
                inversions += 1

    answer = 2 * inversions - (inversions & 1)
    print(f"{answer:.6f}")

if __name__ == "__main__":
    main()