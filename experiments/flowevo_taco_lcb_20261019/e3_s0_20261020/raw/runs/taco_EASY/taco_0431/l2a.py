import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])

    poland = set(data[2:2 + n])
    enemy = set(data[2 + n:2 + n + m])

    common = len(poland & enemy)

    if n + (common % 2) > m:
        print("YES")
    else:
        print("NO")

if __name__ == "__main__":
    main()