import sys


def main() -> None:
    inp = sys.stdin.buffer

    line = inp.readline()
    if not line:
        return

    n = int(line)
    unusual = 0

    # The unusual square over GF(2) equals the XOR of all diagonal entries.
    for i in range(n):
        row = b''.join(inp.readline().split())
        unusual ^= row[i] & 1

    # Read q, skipping possible empty lines.
    q_line = inp.readline()
    while q_line.strip() == b'':
        q_line = inp.readline()
    q = int(q_line)

    answer = bytearray()

    for _ in range(q):
        query = inp.readline()

        # Find the first non-whitespace byte.
        p = 0
        length = len(query)
        while p < length and query[p] <= 32:
            p += 1

        while p == length:
            query = inp.readline()
            length = len(query)
            p = 0
            while p < length and query[p] <= 32:
                p += 1

        if query[p] == 51:  # ASCII '3'
            answer.append(48 + unusual)  # ASCII '0' or '1'
        else:
            # Flipping any row or column flips exactly one diagonal entry.
            unusual ^= 1

    sys.stdout.buffer.write(answer)


if __name__ == "__main__":
    main()