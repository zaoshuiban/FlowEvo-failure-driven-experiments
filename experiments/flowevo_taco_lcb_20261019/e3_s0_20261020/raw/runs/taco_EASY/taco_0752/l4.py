import sys

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []

    for x in data[1:1 + t]:
        # Possible visible pips are 14 * k + top, where k >= 1 and top in [1, 6].
        # This is equivalent to: x >= 15 and (x - 15) % 14 < 6.
        if x >= 15 and (x - 15) % 14 < 6:
            ans.append("YES")
        else:
            ans.append("NO")

    sys.stdout.write("\n".join(ans) + "\n")

if __name__ == "__main__":
    main()