import sys

def main():
    s = sys.stdin.readline().strip()

    vertical = 0  # number of vertical tiles placed in the current cycle
    horizontal = 0  # number of horizontal tiles placed in the current cycle

    ans = []

    for ch in s:
        if ch == '0':  # vertical tile: use column 3
            if vertical % 2 == 0:
                ans.append("1 3")
            else:
                ans.append("3 3")
            vertical += 1
        else:  # horizontal tile: use columns 1 and 2
            row = horizontal % 4 + 1
            ans.append(f"{row} 1")
            horizontal += 1

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()