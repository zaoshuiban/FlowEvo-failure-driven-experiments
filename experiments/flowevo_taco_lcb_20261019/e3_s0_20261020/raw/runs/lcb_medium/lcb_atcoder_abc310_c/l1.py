import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    sticks = set()

    for s in data[1:n + 1]:
        rev = s[::-1]
        if s <= rev:
            sticks.add(s)
        else:
            sticks.add(rev)

    print(len(sticks))

if __name__ == "__main__":
    main()