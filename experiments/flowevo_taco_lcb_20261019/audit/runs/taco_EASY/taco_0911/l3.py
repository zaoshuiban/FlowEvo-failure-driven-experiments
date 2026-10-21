import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    s = data[1] if len(data) > 1 else b""

    keys = [0] * 26
    bought = 0

    pairs = min(n - 1, len(s) // 2)

    for i in range(pairs):
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