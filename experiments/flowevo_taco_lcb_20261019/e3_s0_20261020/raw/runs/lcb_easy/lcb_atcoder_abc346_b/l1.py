import sys

W, B = map(int, sys.stdin.readline().split())

S = "wbwbwwbwbwbw"
length = W + B

for start in range(12):
    white_count = 0
    for i in range(length):
        if S[(start + i) % 12] == 'w':
            white_count += 1

    if white_count == W:
        print("Yes")
        sys.exit()

print("No")