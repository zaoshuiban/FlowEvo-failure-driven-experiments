import sys

def main():
    S, T = sys.stdin.read().split()
    n = len(S)

    for w in range(1, n):
        for c in range(1, w + 1):
            result = []
            for i in range(0, n, w):
                chunk = S[i:i + w]
                if len(chunk) >= c:
                    result.append(chunk[c - 1])

            if ''.join(result) == T:
                print("Yes")
                return

    print("No")

if __name__ == "__main__":
    main()