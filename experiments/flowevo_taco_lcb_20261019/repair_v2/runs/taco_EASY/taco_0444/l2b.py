import sys

def main():
    data = sys.stdin.read().split()
    t = int(data[0])
    ans = []
    idx = 1

    for _ in range(t):
        x = int(data[idx])
        y = int(data[idx + 1])
        idx += 2

        if y % x != 0:
            ans.append("0 0")
        else:
            ans.append(f"1 {y // x}")

    print("\n".join(ans))

if __name__ == "__main__":
    main()