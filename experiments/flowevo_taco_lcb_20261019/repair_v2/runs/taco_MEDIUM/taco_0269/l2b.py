import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    ans = []

    for i in range(1, t + 1):
        n = int(data[i])

        equal_pieces = 'y' if 360 % n == 0 else 'n'
        any_pieces = 'y' if n <= 360 else 'n'
        distinct_pieces = 'y' if n * (n + 1) // 2 <= 360 else 'n'

        ans.append(f"{equal_pieces} {any_pieces} {distinct_pieces}")

    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    solve()