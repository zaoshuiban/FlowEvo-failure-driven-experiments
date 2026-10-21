import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    m = int(data[0])
    bubbly_count = 0

    for word in data[1:m + 1]:
        stack = bytearray()

        for ch in word:
            if stack and stack[-1] == ch:
                stack.pop()
            else:
                stack.append(ch)

        if not stack:
            bubbly_count += 1

    print(bubbly_count)

if __name__ == "__main__":
    main()