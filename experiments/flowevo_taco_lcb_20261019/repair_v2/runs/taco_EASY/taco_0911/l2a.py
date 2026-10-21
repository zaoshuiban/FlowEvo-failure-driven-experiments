import sys

def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    s = data[1]

    keys = [0] * 26
    bought = 0

    for i in range(0, 2 * n - 2, 2):
        key = ord(s[i]) - ord('a')
        keys[key] += 1

        door = ord(s[i + 1]) - ord('A')
        if keys[door] > 0:
            keys[door] -= 1
        else:
            bought += 1

    print(bought)

if __name__ == "__main__":
    main()