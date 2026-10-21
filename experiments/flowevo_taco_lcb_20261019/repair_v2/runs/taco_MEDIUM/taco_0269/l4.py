import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    ans = []

    for n in data[1:1 + t]:
        equal_pieces = 'y' if 360 % n == 0 else 'n'
        any_pieces = 'y' if n <= 360 else 'n'
        distinct_pieces = 'y' if n * (n + 1) // 2 <= 360 else 'n'

        ans.append(f"{equal_pieces} {any_pieces} {distinct_pieces}")

    sys.stdout.write("\n".join(ans))
    if ans:
        sys.stdout.write("\n")


if __name__ == "__main__":
    solve()