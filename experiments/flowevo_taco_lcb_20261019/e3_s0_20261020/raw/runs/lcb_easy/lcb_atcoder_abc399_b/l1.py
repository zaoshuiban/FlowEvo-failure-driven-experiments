import sys

def main():
    data = list(map(int, sys.stdin.read().split()))
    n = data[0]
    p = data[1:1 + n]

    result = []
    for score in p:
        rank = 1 + sum(1 for other in p if other > score)
        result.append(str(rank))

    print("\n".join(result))

if __name__ == "__main__":
    main()