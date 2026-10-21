import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    q = int(data[1])

    # Maximum depth of the complete binary tree.
    height = (n + 1).bit_length() - 2

    answers = []
    idx = 2

    for _ in range(q):
        u = int(data[idx])
        path = data[idx + 1]
        idx += 2

        current = u

        # Depth of vertex u:
        # labels at depth d are odd multiples of 2^(height - d).
        trailing_zeros = (current & -current).bit_length() - 1
        depth = height - trailing_zeros

        for ch in path:
            if ch == ord('L'):
                if depth < height:
                    step = 1 << (height - depth - 1)
                    current -= step
                    depth += 1

            elif ch == ord('R'):
                if depth < height:
                    step = 1 << (height - depth - 1)
                    current += step
                    depth += 1

            elif ch == ord('U'):
                if depth > 0:
                    shift = height - depth
                    step = 1 << shift

                    # If the node is a left child, its index divided by step is 1 mod 4.
                    if ((current >> shift) & 3) == 1:
                        current += step
                    else:
                        current -= step

                    depth -= 1

        answers.append(str(current))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()