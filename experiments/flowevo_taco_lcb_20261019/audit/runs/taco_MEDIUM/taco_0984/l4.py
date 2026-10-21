import sys

def main():
    s = sys.stdin.readline().strip()
    ans = []

    vertical = 0
    horizontal = 0

    for ch in s:
        if ch == '0':  # vertical 2x1 tile
            row = 1 if vertical % 2 == 0 else 3
            ans.append(f"{row} 1")
            vertical += 1
        else:          # horizontal 1x2 tile
            row = horizontal % 4 + 1
            ans.append(f"{row} 3")
            horizontal += 1

    sys.stdout.write("\n".join(ans))
    if ans:
        sys.stdout.write("\n")

if __name__ == "__main__":
    main()