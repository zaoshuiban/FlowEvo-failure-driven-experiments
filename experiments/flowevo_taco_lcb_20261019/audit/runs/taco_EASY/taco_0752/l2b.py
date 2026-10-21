import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []

    for x in data[1:1 + t]:
        remainder = x % 14
        if x >= 15 and 1 <= remainder <= 6:
            ans.append("YES")
        else:
            ans.append("NO")

    print("\n".join(ans))

if __name__ == "__main__":
    main()