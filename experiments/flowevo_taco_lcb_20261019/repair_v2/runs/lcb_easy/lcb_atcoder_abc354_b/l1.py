import sys

def main():
    input = sys.stdin.readline
    n = int(input())
    users = []

    total = 0
    for _ in range(n):
        s, c = input().split()
        c = int(c)
        users.append(s)
        total += c

    users.sort()
    print(users[total % n])

if __name__ == "__main__":
    main()