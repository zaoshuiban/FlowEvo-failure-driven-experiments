import sys

X = int(sys.stdin.readline())

factorial = 1
n = 1

while factorial < X:
    n += 1
    factorial *= n

print(n)