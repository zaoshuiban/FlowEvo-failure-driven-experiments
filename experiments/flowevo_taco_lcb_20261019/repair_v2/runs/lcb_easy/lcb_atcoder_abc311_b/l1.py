import sys

def main():
    input = sys.stdin.readline
    N, D = map(int, input().split())
    S = [input().strip() for _ in range(N)]

    ans = 0
    current = 0

    for j in range(D):
        if all(S[i][j] == 'o' for i in range(N)):
            current += 1
            ans = max(ans, current)
        else:
            current = 0

    print(ans)

if __name__ == "__main__":
    main()