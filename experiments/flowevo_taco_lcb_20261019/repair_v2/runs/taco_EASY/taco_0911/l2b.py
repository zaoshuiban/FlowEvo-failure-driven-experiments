import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    s = data[1]

    keys = [0] * 26
    bought = 0

    for i in range(0, 2 * n - 2, 2):
        key_type = ord(s[i]) - ord('a')
        keys[key_type] += 1

        door_type = ord(s[i + 1]) - ord('A')
        if keys[door_type] > 0:
            keys[door_type] -= 1
        else:
            bought += 1

    print(bought)

if __name__ == "__main__":
    main()