import sys

def main():
    data = sys.stdin.read().split()
    t = int(data[0])
    ans = []

    for i in range(1, t + 1):
        s = data[i]
        first = ord(s[0]) - ord('a')
        second = ord(s[1]) - ord('a')

        index = first * 25 + second + (1 if second < first else 0)
        ans.append(str(index))

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()