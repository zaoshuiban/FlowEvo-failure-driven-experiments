import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    idx = 1
    prerequisites = [[] for _ in range(n + 1)]

    for i in range(1, n + 1):
        c = data[idx]
        idx += 1
        prerequisites[i] = data[idx:idx + c]
        idx += c

    visited = bytearray(n + 1)
    visited[1] = 1

    order = []
    stack = [(1, 0)]

    while stack:
        book, pos = stack[-1]

        if pos < len(prerequisites[book]):
            nxt = prerequisites[book][pos]
            stack[-1] = (book, pos + 1)

            if not visited[nxt]:
                visited[nxt] = 1
                stack.append((nxt, 0))
        else:
            order.append(book)
            stack.pop()

    answer = [str(book) for book in order if book != 1]
    print(" ".join(answer))

if __name__ == "__main__":
    main()