import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    N = int(data[0])
    M = int(data[1])

    S = data[2:2 + N]
    T = data[2 + N:2 + N + M]

    for a in range(N - M + 1):
        for b in range(N - M + 1):
            match = True
            for i in range(M):
                if S[a + i][b:b + M] != T[i]:
                    match = False
                    break
            if match:
                print(a + 1, b + 1)
                return

if __name__ == "__main__":
    main()