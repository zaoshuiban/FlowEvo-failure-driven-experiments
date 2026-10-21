import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    ax, ay = data[1], data[2]
    bx, by = data[3], data[4]
    cx, cy = data[5], data[6]

    if (ax - bx) * (ax - cx) > 0 and (ay - by) * (ay - cy) > 0:
        print("YES")
    else:
        print("NO")

if __name__ == "__main__":
    main()