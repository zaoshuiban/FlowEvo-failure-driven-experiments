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

        if old in current_to_original:
            original = current_to_original.pop(old)
        else:
            original = old

        current_to_original[new] = original

    ans = [str(len(current_to_original)).encode()]
    for current in sorted(current_to_original):
        ans.append(current_to_original[current] + b" " + current)

    sys.stdout.buffer.write(b"\n".join(ans))

if __name__ == "__main__":
    main()