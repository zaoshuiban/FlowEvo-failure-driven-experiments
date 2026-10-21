import sys


def main() -> None:
    inp = sys.stdin.buffer

    n = int(inp.readline())
    unusual = 0

    for i in range(n):
        row = inp.readline().split()
        unusual ^= row[i][0] & 1

    q = int(inp.readline())
    answer = bytearray()

    for _ in range(q):
        query = inp.readline()
        if query[0] == ord('3'):
            answer.append(ord('0') + unusual)
        else:
            unusual ^= 1

    sys.stdout.buffer.write(answer)


if __name__ == "__main__":
    main()