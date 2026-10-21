import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []
    idx = 1

    for _ in range(t):
        a, b = data[idx], data[idx + 1]
        idx += 2

        if a % 2 == 1 and b % 2 == 1:
            ans.append("Vanka")
        else:
            ans.append("Tuzik")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()