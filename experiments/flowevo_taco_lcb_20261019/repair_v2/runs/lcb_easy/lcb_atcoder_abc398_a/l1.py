import sys

N = int(sys.stdin.readline())

if N % 2 == 1:
    half = N // 2
    ans = '-' * half + '=' + '-' * half
else:
    half = N // 2 - 1
    ans = '-' * half + '==' + '-' * half

print(ans)