import sys

def main():
    input = sys.stdin.readline
    n = int(input())
    strings = [input().strip() for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            t = strings[i] + strings[j]
            if t == t[::-1]:
                print("Yes")
                return

    print("No")

if __name__ == "__main__":
    main()