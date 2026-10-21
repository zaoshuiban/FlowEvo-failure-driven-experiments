import sys

def main():
    n, h = map(int, sys.stdin.readline().split())

    # Total number of BSTs with n nodes: Catalan number C_n
    catalan = [0] * (n + 1)
    catalan[0] = 1
    for size in range(1, n + 1):
        total = 0
        for left in range(size):
            total += catalan[left] * catalan[size - 1 - left]
        catalan[size] = total

    # cur[size] = number of BSTs with 'size' nodes and height <= current_limit
    # Initially current_limit = 0: only the empty tree has height <= 0.
    cur = [0] * (n + 1)
    cur[0] = 1

    # Count trees with height <= h - 1
    for _ in range(h - 1):
        nxt = [0] * (n + 1)
        nxt[0] = 1
        for size in range(1, n + 1):
            total = 0
            for left in range(size):
                right = size - 1 - left
                total += cur[left] * cur[right]
            nxt[size] = total
        cur = nxt

    answer = catalan[n] - cur[n]
    print(answer)

if __name__ == "__main__":
    main()