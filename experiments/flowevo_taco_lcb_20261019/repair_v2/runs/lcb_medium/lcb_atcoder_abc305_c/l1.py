import sys

def main():
    input = sys.stdin.readline

    H, W = map(int, input().split())
    S = [input().strip() for _ in range(H)]

    top, bottom = H, -1
    left, right = W, -1

    for i in range(H):
        for j in range(W):
            if S[i][j] == '#':
                top = min(top, i)
                bottom = max(bottom, i)
                left = min(left, j)
                right = max(right, j)

    for i in range(top, bottom + 1):
        for j in range(left, right + 1):
            if S[i][j] == '.':
                print(i + 1, j + 1)
                return

if __name__ == "__main__":
    main()