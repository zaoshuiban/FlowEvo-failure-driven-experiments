import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, k = data[0], data[1]
    participations = data[2:2 + n]

    eligible = sum(1 for y in participations if y + k <= 5)
    print(eligible // 3)

if __name__ == "__main__":
    main()