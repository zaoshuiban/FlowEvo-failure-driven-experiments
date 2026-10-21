import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:1 + n]

    maximum = max(a)
    answer = max(x for x in a if x < maximum)

    print(answer)

if __name__ == "__main__":
    main()