import sys

def main():
    input = sys.stdin.readline
    N = int(input())
    wins = []

    for _ in range(N):
        s = input().strip()
        wins.append(s.count('o'))

    players = list(range(1, N + 1))
    players.sort(key=lambda p: (-wins[p - 1], p))

    print(*players)

if __name__ == "__main__":
    main()