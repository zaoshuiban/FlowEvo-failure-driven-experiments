import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    t = int(data[1])
    s = list(data[2].decode())

    for _ in range(t):
        i = 0
        while i + 1 < n:
            if s[i] == 'B' and s[i + 1] == 'G':
                s[i], s[i + 1] = s[i + 1], s[i]
                i += 2
            else:
                i += 1

    sys.stdout.write(''.join(s) + '\n')

if __name__ == "__main__":
    main()