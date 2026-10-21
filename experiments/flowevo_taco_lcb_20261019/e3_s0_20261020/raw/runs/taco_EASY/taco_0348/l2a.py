import sys

def main():
    H, L = map(int, sys.stdin.readline().split())
    depth = (L * L - H * H) / (2.0 * H)
    print(f"{depth:.13f}")

if __name__ == "__main__":
    main()