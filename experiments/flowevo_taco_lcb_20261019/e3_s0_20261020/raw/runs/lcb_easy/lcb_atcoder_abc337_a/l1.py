import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    takahashi = 0
    aoki = 0

    idx = 1
    for _ in range(n):
        takahashi += data[idx]
        aoki += data[idx + 1]
        idx += 2

    if takahashi > aoki:
        print("Takahashi")
    elif takahashi < aoki:
        print("Aoki")
    else:
        print("Draw")

if __name__ == "__main__":
    main()