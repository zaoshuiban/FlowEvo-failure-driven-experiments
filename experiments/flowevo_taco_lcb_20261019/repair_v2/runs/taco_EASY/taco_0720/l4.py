import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    q = int(data[0])
    current_to_original = {}
    idx = 1

    for _ in range(q):
        old = data[idx]
        new = data[idx + 1]
        idx += 2

        original = current_to_original.pop(old, old)
        current_to_original[new] = original

    lines = [str(len(current_to_original)).encode()]
    for current, original in current_to_original.items():
        lines.append(original + b" " + current)

    sys.stdout.buffer.write(b"\n".join(lines) + b"\n")

if __name__ == "__main__":
    main()