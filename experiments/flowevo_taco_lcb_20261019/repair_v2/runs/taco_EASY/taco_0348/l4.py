import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    H = int(data[0])
    L = int(data[1])

    depth = (L * L - H * H) / (2 * H)
    sys.stdout.write(f"{depth:.13f}\n")

if __name__ == "__main__":
    main()