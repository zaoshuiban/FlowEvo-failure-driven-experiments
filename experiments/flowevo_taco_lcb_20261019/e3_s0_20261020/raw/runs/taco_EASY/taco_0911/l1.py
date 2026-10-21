import sys

def main():
    input = sys.stdin.readline
    n = int(input())
    s = input().strip()

    keys = [0] * 26
    answer = 0

    for i in range(0, 2 * n - 2, 2):
        keys[ord(s[i]) - ord('a')] += 1

        door = ord(s[i + 1]) - ord('A')
        if keys[door] > 0:
            keys[door] -= 1
        else:
            answer += 1

    print(answer)

if __name__ == "__main__":
    main()