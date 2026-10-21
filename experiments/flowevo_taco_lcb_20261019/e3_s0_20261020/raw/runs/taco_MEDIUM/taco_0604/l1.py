import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    m = int(data[0])
    answer = 0

    for i in range(1, m + 1):
        word = data[i]
        stack = []

        for ch in word:
            if stack and stack[-1] == ch:
                stack.pop()
            else:
                stack.append(ch)

        if not stack:
            answer += 1

    print(answer)

if __name__ == "__main__":
    main()