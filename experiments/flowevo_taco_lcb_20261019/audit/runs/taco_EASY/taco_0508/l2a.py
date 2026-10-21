import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    ans = []
    for n in data[1:t + 1]:
        ans.append("YES" if n % 4 == 0 else "NO")
    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()