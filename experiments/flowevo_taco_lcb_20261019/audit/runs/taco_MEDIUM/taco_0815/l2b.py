import sys

def main():
    data = sys.stdin.read().strip().split()
    if not data:
        return

    t = int(data[0])
    ans = []
    idx = 1

    for _ in range(t):
        a = int(data[idx])
        b = int(data[idx + 1])
        idx += 2

        probability = (a - b) / (a + b)
        ans.append(f"{probability:.12f}")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()