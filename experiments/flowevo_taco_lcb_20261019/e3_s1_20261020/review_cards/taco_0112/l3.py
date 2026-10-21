import sys


def canonical(s: bytes) -> bytes:
    n = len(s)
    if n & 1:
        return s

    # Length of the smallest block that cannot be split anymore.
    block_len = n
    while block_len % 2 == 0:
        block_len //= 2

    blocks = [
        s[i * block_len:(i + 1) * block_len]
        for i in range(n // block_len)
    ]

    while len(blocks) > 1:
        next_blocks = []
        for i in range(0, len(blocks), 2):
            a = blocks[i]
            b = blocks[i + 1]
            if a < b:
                next_blocks.append(a + b)
            else:
                next_blocks.append(b + a)
        blocks = next_blocks

    return blocks[0]


def main() -> None:
    data = sys.stdin.buffer.read().split()
    s1, s2 = data[0], data[1]

    if s1 == s2 or canonical(s1) == canonical(s2):
        print("YES")
    else:
        print("NO")


if __name__ == "__main__":
    main()