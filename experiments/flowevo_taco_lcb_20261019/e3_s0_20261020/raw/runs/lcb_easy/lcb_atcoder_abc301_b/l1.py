import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:1 + n]

    ans = [a[0]]
    prev = a[0]

    for cur in a[1:]:
        if prev < cur:
            for x in range(prev + 1, cur + 1):
                ans.append(x)
        else:
            for x in range(prev - 1, cur - 1, -1):
                ans.append(x)
        prev = cur

    print(*ans)

if __name__ == "__main__":
    main()