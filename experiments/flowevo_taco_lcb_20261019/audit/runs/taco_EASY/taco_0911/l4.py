import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    s = b''.join(data[1:])

    keys = [0] * 26
    bought = 0

    for i in range(n - 1):
        key = s[2 * i] - ord('a')
        door = s[2 * i + 1] - ord('A')

        keys[key] += 1

        if keys[door] > 0:
            keys[door] -= 1
        else:
            bought += 1

    print(bought)

if __name__ == "__main__":
    main()