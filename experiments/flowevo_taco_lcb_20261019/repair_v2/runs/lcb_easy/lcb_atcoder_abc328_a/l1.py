import sys

def main():
    data = list(map(int, sys.stdin.read().split()))
    N, X = data[0], data[1]
    scores = data[2:2 + N]
    print(sum(s for s in scores if s <= X))

if __name__ == "__main__":
    main()