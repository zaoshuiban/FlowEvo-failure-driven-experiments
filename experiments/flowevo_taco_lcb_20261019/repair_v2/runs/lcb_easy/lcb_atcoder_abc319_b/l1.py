import sys

def main():
    N = int(sys.stdin.readline().strip())
    ans = []

    for i in range(N + 1):
        for j in range(1, 10):
            if N % j == 0 and i % (N // j) == 0:
                ans.append(str(j))
                break
        else:
            ans.append('-')

    print(''.join(ans))

if __name__ == "__main__":
    main()