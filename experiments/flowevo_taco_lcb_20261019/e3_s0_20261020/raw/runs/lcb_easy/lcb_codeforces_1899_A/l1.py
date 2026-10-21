import sys

def main():
    data = list(map(int, sys.stdin.read().split()))
    if not data:
        return

    t = data[0]
    ans = []

    for n in data[1:1 + t]:
        if n % 3 == 0:
            ans.append("Second")
        else:
            ans.append("First")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()