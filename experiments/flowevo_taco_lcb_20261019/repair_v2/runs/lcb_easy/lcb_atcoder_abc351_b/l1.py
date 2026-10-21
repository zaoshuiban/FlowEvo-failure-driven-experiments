import sys

def main():
    input = sys.stdin.readline

    N = int(input())
    A = [input().strip() for _ in range(N)]

    for i in range(N):
        B_row = input().strip()

        if A[i] != B_row:
            for j in range(N):
                if A[i][j] != B_row[j]:
                    print(i + 1, j + 1)
                    return

if __name__ == "__main__":
    main()