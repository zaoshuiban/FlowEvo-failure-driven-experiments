import sys


def solve() -> None:
    data = sys.stdin.buffer
    first = data.readline().split()
    if not first:
        return

    n, m = map(int, first)
    name_to_idx = {}
    instructions = []

    for i in range(n):
        parts = data.readline().split()
        name = parts[0]

        if len(parts) == 3:
            const = parts[2]
            instructions.append((0, const))
        else:
            left = parts[2]
            op_token = parts[3]
            right = parts[4]

            a = -1 if left == b'?' else name_to_idx[left]
            b = -1 if right == b'?' else name_to_idx[right]

            if op_token == b'AND':
                op = 0
            elif op_token == b'OR':
                op = 1
            else:
                op = 2

            instructions.append((1, op, a, b))

        name_to_idx[name] = i

    min_answer = bytearray(b'0' * m)
    max_answer = bytearray(b'0' * m)

    vals0 = [0] * n
    vals1 = [0] * n

    for pos in range(m):
        count0 = 0
        count1 = 0

        for i, instruction in enumerate(instructions):
            if instruction[0] == 0:
                bit = instruction[1][pos] - 48
                vals0[i] = bit
                vals1[i] = bit
                count0 += bit
                count1 += bit
            else:
                _, op, a, b = instruction

                if a == -1:
                    a0, a1 = 0, 1
                else:
                    a0, a1 = vals0[a], vals1[a]

                if b == -1:
                    b0, b1 = 0, 1
                else:
                    b0, b1 = vals0[b], vals1[b]

                if op == 0:
                    c0 = a0 & b0
                    c1 = a1 & b1
                elif op == 1:
                    c0 = a0 | b0
                    c1 = a1 | b1
                else:
                    c0 = a0 ^ b0
                    c1 = a1 ^ b1

                vals0[i] = c0
                vals1[i] = c1
                count0 += c0
                count1 += c1

        if count0 <= count1:
            min_answer[pos] = ord('0')
        else:
            min_answer[pos] = ord('1')

        if count1 > count0:
            max_answer[pos] = ord('1')
        else:
            max_answer[pos] = ord('0')

    output = bytes(min_answer) + b'\n' + bytes(max_answer) + b'\n'
    sys.stdout.buffer.write(output)


if __name__ == "__main__":
    solve()