import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []

    for x in data[1:1 + t]:
        r = x % 14
        if x > 14 and 1 <= r <= 6:
            ans.append("YES")
        else:
            ans.append("NO")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()