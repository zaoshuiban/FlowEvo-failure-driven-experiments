import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    H = int(data[0])
    L = int(data[1])

    depth = (L * L - H * H) / (2.0 * H)
    print(f"{depth:.15f}")

if __name__ == "__main__":
    main()