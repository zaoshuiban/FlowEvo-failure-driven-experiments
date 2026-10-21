import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    idx = 1
    output = []

    for i in range(n):
        row = data[idx:idx + n]
        idx += n

        connected = [str(j + 1) for j, value in enumerate(row) if value == 1]
        output.append(" ".join(connected))

    sys.stdout.write("\n".join(output) + "\n")

if __name__ == "__main__":
    main()