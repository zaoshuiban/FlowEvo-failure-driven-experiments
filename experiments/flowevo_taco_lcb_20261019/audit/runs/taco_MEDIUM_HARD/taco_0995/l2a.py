import sys

def solve() -> None:
    input = sys.stdin.buffer.readline

    n = int(input())
    diagonal_parity = 0

    for i in range(n):
        row = input().split()
        diagonal_parity ^= row[i][0] - ord('0')

    q = int(input())
    answers = bytearray()

    for _ in range(q):
        query = input()
        if query[0] == ord('3'):
            answers.append(ord('0') + diagonal_parity)
        else:
            diagonal_parity ^= 1

    sys.stdout.buffer.write(answers)
    sys.stdout.buffer.write(b'\n')


if __name__ == "__main__":
    solve()